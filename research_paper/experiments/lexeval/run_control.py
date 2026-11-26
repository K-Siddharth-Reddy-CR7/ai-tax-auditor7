"""Permanent TEST run controls (Phase C) with run-log reconciliation and code identity (Phase C.1).

An authorised TEST evaluation is the only way TEST rows may be scored. `open_run()`:
  1. verifies the frozen manifest: benchmark files, excluded_items.csv, config, review-treatments file,
     evaluation-exclusions file, and the CODE IDENTITY (see CODE_IDENTITY_PATTERNS) pinned at freeze;
  2. requires a clean git working tree whose HEAD is the frozen commit or a descendant that changes no
     code-identity path;
  3. reconciles the append-only run log with the run directories and recovery records (`reconcile`);
  4. requires --authorised-by for every run, and --rerun-reason if any earlier run evidence exists;
  5. creates a new permanent run directory and appends a 'started' entry.
`close_run()` re-verifies the manifest (a failure closes the run as 'aborted' and raises), records output
hashes, writes close.json, makes the outputs read-only, and appends the end entry.

Reconciliation (`reconcile`) refuses on: a missing log while run or recovery evidence exists; a broken hash
chain (edited, removed, inserted, duplicated or reordered lines); a truncated last line; whole entries removed
from the end (the run directory or its close.json no longer matches the log); orphaned run directories; log
entries without a run directory; missing, corrupt or modified run.json/close.json/outputs; duplicated or
out-of-order events; wrong previous-run references; malformed run IDs; corrupt, missing, modified or
unacknowledged recovery records; changes to acknowledged runs after their recovery. An interrupted run (started,
never closed) reconciles, but a new TEST run is refused until it has been acknowledged by a recovery.

Recovery protocol (Phase C.2; `recover`, `--stage recover-runs --authorised-by --recovery-reason`):
- Allowed only when reconciliation fails or an interrupted run is unacknowledged. Nothing is ever deleted,
  repaired, rewritten or reconstructed; no historical 'started'/'completed' entry is ever fabricated.
- Each recovery writes ONE new record results/run_recoveries/<id>.json (exclusive create) with a sequence number
  and appends one 'recovery' entry to the log (a missing log is never regenerated: a new log then starts with
  this entry, and the record says so). The record snapshots ALL surviving evidence: the exact log bytes (hash,
  line count; the prefix is then preserved byte-for-byte), an inventory with SHA-256 of every file of every
  run directory, every earlier recovery record (by id, sequence and hash, marked present-verified,
  present-unverifiable or missing), run IDs known only from the log or from earlier records, and the problems
  found. It classifies each run's history as log entries present or missing.
- The records form a chain: the latest record lists every earlier record (sequence 1..n-1) with its hash, and
  the latest record itself is bound to its log entry. Losing the log or an earlier recovery entry therefore
  leaves a recoverable state: the next recovery acknowledges the earlier records it can still see (and those
  it can only name) instead of failing.
- Fails closed (writes nothing) when the evidence is contradictory: a recovery record that is unreadable, two
  records with the same sequence number, or a record whose bytes differ from the hash recorded for it by the
  log or by another record. Resolving that would mean choosing between conflicting histories; restore the
  original record from version control first.
- After a recovery, every acknowledged run directory must stay byte-identical to its inventory (missing,
  modified and added files are detected). For an interrupted run this is the protection point of its outputs.

What a recovery does NOT establish: that missing log entries or records said what they are assumed to say,
that files were intact before the recovery (recovery-time hashes only protect them from then on), or that a
record with no surviving independent hash was not altered before the recovery (it is marked
present-unverifiable).

LIMITS (trust boundary): all of this is local evidence. The hash chain has no secret key. Anyone able to rewrite
every local file (log, run directories, recovery records) consistently can produce an undetectable history;
deleting ALL evidence is also undetectable locally. These controls detect accidental and casual changes and make
the sanctioned route the only one this code accepts; they are not cryptographic proof. Committing the run
directories, log and recovery records to git, and the authors' own records, are the external check.
"""
import datetime
import glob
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import stat
import subprocess

from .paths import EXP, GEN, PILOT, REPO, RESULTS

DATA_FILES = ["product_benchmark.csv", "country_benchmark.csv", "malformed_inputs.csv"]
EXCLUDED_FILE = "excluded_items.csv"
GENESIS = "0" * 64
RUN_ID_RE = re.compile(r"^\d{8}T\d{6}Z-[0-9a-f]{8}$")
END_EVENTS = ("completed", "aborted")

# Code identity pinned at freeze (paths relative to the repository root). Included: the evaluation code, the
# three systems' code, the dependency pins, and the original tables that B/S0/S1 read at run time.
# Excluded: tests, documentation, __pycache__, results/, data/generated (hashed separately), config.json
# (hashed separately), frontend. "**/" matches zero or more directories, so nested packages are included.
CODE_IDENTITY_PATTERNS = [
    "research_paper/experiments/run_all.py",
    "research_paper/experiments/lexeval/**/*.py",
    "research_paper/experiments/requirements.txt",
    "backend/server.py",
    "backend/lexitax_v2/**/*.py",
    "backend/requirements.txt",
    "backend/requirements-research.txt",
    "products.json",
    "taxes.json",
    "trade_policies.json",
    "sample_transactions.json",
]


class RunControlError(RuntimeError):
    """A TEST run (or freeze, or recovery) was refused."""


class RunPaths:
    """All inputs of a TEST run. Defaults are the production locations; tests pass temporary ones."""

    def __init__(self, gen=None, manifest=None, config=None, treatments=None, exclusions=None, pilot=None,
                 results=None, code_root=None):
        self.gen = gen or GEN
        self.manifest = manifest or os.path.join(self.gen, "MANIFEST.json")
        self.config = config or os.path.join(EXP, "config.json")
        self.treatments = treatments or os.path.join(PILOT, "authorised_review_treatments_v1.csv")
        self.exclusions = exclusions or os.path.join(EXP, "evaluation_exclusions_v1.json")
        self.pilot = pilot or PILOT
        self.results = results or RESULTS
        self.code_root = code_root or REPO
        self.tuning = os.path.join(self.results, "tuning_dev.json")
        self.runs = os.path.join(self.results, "runs")
        self.log = os.path.join(self.results, "test_runs.jsonl")
        self.recoveries = os.path.join(self.results, "run_recoveries")


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def _json_sha(obj):
    return _sha_bytes(json.dumps(obj, sort_keys=True).encode())


# ------------------------------------------------------------------------------------------ code identity
def _pattern_regex(pat):
    """Translate an identity pattern to a regex with the same meaning as glob(recursive=True):
    '**/' = zero or more directories, '*' = any characters except '/'."""
    out, i = "", 0
    while i < len(pat):
        if pat.startswith("**/", i):
            out, i = out + "(?:[^/]+/)*", i + 3
        elif pat[i] == "*":
            out, i = out + "[^/]*", i + 1
        else:
            out, i = out + re.escape(pat[i]), i + 1
    return re.compile(out + r"\Z")


_IDENTITY_RES = [_pattern_regex(p) for p in CODE_IDENTITY_PATTERNS]


def code_identity(code_root):
    files = {}
    for pat in CODE_IDENTITY_PATTERNS:
        for p in glob.glob(os.path.join(code_root, pat), recursive=True):
            if os.path.isfile(p):
                files[os.path.relpath(p, code_root).replace(os.sep, "/")] = sha256_file(p)
    combined = _sha_bytes("".join(f"{k}\0{v}\n" for k, v in sorted(files.items())).encode())
    return {"patterns": list(CODE_IDENTITY_PATTERNS), "files": dict(sorted(files.items())), "sha256": combined}


def _git(code_root, *args):
    try:
        r = subprocess.run(["git", "-C", code_root, *args], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None, None
    return r.returncode, r.stdout.strip()


def git_state(code_root):
    rc, head = _git(code_root, "rev-parse", "HEAD")
    rc2, porcelain = _git(code_root, "status", "--porcelain", "--untracked-files=all")
    ok = rc == 0 and rc2 == 0
    return {"commit": head if ok else None, "clean": ok and porcelain == "",
            "dirty_paths": porcelain.splitlines()[:50] if ok and porcelain else []}


def _matches_identity(path):
    return any(r.match(path) for r in _IDENTITY_RES)


def verify_code(paths, man):
    """Problems if the current code differs from the code identity pinned at freeze."""
    ci = man.get("code_identity")
    if not ci or not ci.get("sha256") or not ci.get("git_commit"):
        return ["manifest does not record code_identity (sha256 and git_commit)"]
    problems = []
    cur = code_identity(paths.code_root)
    if cur["sha256"] != ci["sha256"]:
        old, new = ci.get("files", {}), cur["files"]
        changed = sorted(k for k in set(old) & set(new) if old[k] != new[k])
        problems.append(f"code changed since freezing: modified {changed}, added {sorted(set(new) - set(old))}, "
                        f"deleted {sorted(set(old) - set(new))}")
    gs = git_state(paths.code_root)
    if gs["commit"] is None:
        problems.append("git is unavailable; the frozen commit cannot be verified")
    elif gs["commit"] != ci["git_commit"]:
        rc, _ = _git(paths.code_root, "merge-base", "--is-ancestor", ci["git_commit"], gs["commit"])
        if rc != 0:
            problems.append(f"HEAD {gs['commit'][:12]} does not descend from the frozen commit {ci['git_commit'][:12]}")
        else:
            rc, diff = _git(paths.code_root, "diff", "--name-only", ci["git_commit"], gs["commit"])
            touched = sorted(p for p in (diff or "").splitlines() if _matches_identity(p))
            if rc != 0 or touched:
                problems.append(f"commits after the freeze change code-identity paths: {touched}")
    return problems


def manifest_record(paths, approved_by, now=None):
    """The freeze manifest for the current state. Refuses unless the git working tree is clean."""
    if not str(approved_by or "").strip():
        raise RunControlError("--approved-by is required")
    gs = git_state(paths.code_root)
    if gs["commit"] is None:
        raise RunControlError("git is unavailable; cannot pin the code identity")
    if not gs["clean"]:
        raise RunControlError(f"git working tree is not clean; commit or remove: {gs['dirty_paths']}")
    files = {}
    for f in DATA_FILES + [EXCLUDED_FILE]:
        p = os.path.join(paths.gen, f)
        if not os.path.exists(p):
            raise RunControlError(f"cannot freeze: {f} missing")
        files[f] = sha256_file(p)
    ci = code_identity(paths.code_root)
    ci["git_commit"] = gs["commit"]
    return {"approved_by": approved_by,
            "frozen_utc": (now or datetime.datetime.now(datetime.timezone.utc)).isoformat(),
            "files": files, "config_sha256": sha256_file(paths.config),
            "review_treatments_sha256": sha256_file(paths.treatments),
            "evaluation_exclusions_sha256": sha256_file(paths.exclusions), "code_identity": ci}


def verify_manifest(paths):
    """Return the manifest if every recorded hash (data, configuration, code identity) matches; else raise."""
    if not os.path.exists(paths.manifest):
        raise RunControlError("benchmarks are not frozen: MANIFEST.json not found")
    try:
        with open(paths.manifest, encoding="utf-8") as fh:
            man = json.load(fh)
    except (OSError, ValueError) as e:
        raise RunControlError(f"manifest unreadable: {type(e).__name__}: {e}") from e
    if not isinstance(man, dict):
        raise RunControlError("manifest unreadable: not a JSON object")
    problems = []
    if not str(man.get("approved_by", "")).strip():
        problems.append("manifest lacks approved_by")
    files = man.get("files") or {}
    for f in DATA_FILES + [EXCLUDED_FILE]:
        if f not in files:
            problems.append(f"manifest does not record {f}")
    for f, h in sorted(files.items()):
        p = os.path.join(paths.gen, f)
        if not os.path.exists(p) or sha256_file(p) != h:
            problems.append(f"frozen file missing or changed since freezing: {f}")
    for key, path in (("config_sha256", paths.config), ("review_treatments_sha256", paths.treatments),
                      ("evaluation_exclusions_sha256", paths.exclusions)):
        if not man.get(key):
            problems.append(f"manifest does not record {key}")
        elif not os.path.exists(path) or sha256_file(path) != man[key]:
            problems.append(f"{os.path.basename(path)} does not match the manifest ({key})")
    problems += verify_code(paths, man)
    if problems:
        raise RunControlError("manifest verification failed:\n  - " + "\n  - ".join(problems))
    return man


def environment():
    pkgs = {}
    for d in importlib.metadata.distributions():
        name = d.metadata.get("Name")
        if name:
            pkgs[name.lower()] = d.version
    return {"python": platform.python_version(), "implementation": platform.python_implementation(),
            "platform": platform.platform(), "packages": dict(sorted(pkgs.items()))}


# ------------------------------------------------------------------------------------- log and reconciliation
def _read_lines(path):
    with open(path, "rb") as fh:
        data = fh.read()
    return data, data.splitlines()


def read_log(path):
    """Strict parse of a log with no recovery anchor: hash chain verified from the first line."""
    if not os.path.exists(path):
        return []
    data, lines = _read_lines(path)
    if data and not data.endswith(b"\n"):
        raise RunControlError("run log is truncated or was edited (no trailing newline)")
    entries, prev = [], GENESIS
    for n, line in enumerate(lines, 1):
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            raise RunControlError(f"run log line {n} is not valid JSON") from None
        if e.get("prev_sha256") != prev:
            raise RunControlError(f"run log hash chain broken at line {n} (an entry was edited or removed)")
        prev = _sha_bytes(line)
        entries.append(e)
    return entries


RECOVERY_SCHEMA = "lexitax-run-recovery/2"
RECORD_KEYS = ("schema", "recovery_id", "seq", "prior_recoveries", "runs", "runs_without_directory", "log")


def _inventory(d):
    """Every file under a run directory with its SHA-256 (relative POSIX paths, sorted)."""
    files = {}
    for root, _, fs in os.walk(d):
        for f in fs:
            p = os.path.join(root, f)
            files[os.path.relpath(p, d).replace(os.sep, "/")] = sha256_file(p)
    return dict(sorted(files.items()))


def _inventory_diff(old, new):
    return {"modified": sorted(k for k in set(old) & set(new) if old[k] != new[k]),
            "deleted": sorted(set(old) - set(new)), "added": sorted(set(new) - set(old))}


def _prefix_sha(lines):
    return _sha_bytes(b"".join(line + b"\n" for line in lines))


def _strip(e):
    return {k: v for k, v in e.items() if k not in ("event", "prev_sha256")}


def _load_records(paths):
    """(valid {recovery_id: (record, sha, path)}, corrupt [file names]) from results/run_recoveries/."""
    valid, corrupt = {}, []
    if not os.path.isdir(paths.recoveries):
        return valid, corrupt
    for f in sorted(os.listdir(paths.recoveries)):
        p = os.path.join(paths.recoveries, f)
        try:
            rec = json.load(open(p, encoding="utf-8"))
            ok = (isinstance(rec, dict) and rec.get("schema") == RECOVERY_SCHEMA and all(k in rec for k in RECORD_KEYS)
                  and isinstance(rec["seq"], int) and rec["seq"] >= 1 and f == f"{rec['recovery_id']}.json")
        except (OSError, ValueError):
            ok = False
        if ok:
            valid[rec["recovery_id"]] = (rec, sha256_file(p), p)
        else:
            corrupt.append(f)
    return valid, corrupt


def _parse_lines(lines):
    out = []
    for line in lines:
        try:
            e = json.loads(line)
            out.append(e if isinstance(e, dict) else None)
        except ValueError:
            out.append(None)
    return out


def reconcile(paths):
    """Check that the log, run directories and recovery records agree. Returns {"previous": [run ids in
    order], "status": {run_id: started|completed|aborted|acknowledged}, "interrupted": [run ids started but
    never closed and not yet acknowledged]}; raises RunControlError listing every problem otherwise."""
    problems = []
    entries = sorted(os.listdir(paths.runs)) if os.path.isdir(paths.runs) else []
    for d in entries:
        if not os.path.isdir(os.path.join(paths.runs, d)):
            problems.append(f"unexpected file in runs/: {d}")
    run_dirs = [d for d in entries if os.path.isdir(os.path.join(paths.runs, d))]
    records, corrupt = _load_records(paths)
    for f in corrupt:
        problems.append(f"recovery record {f} is corrupt or unreadable")

    if not os.path.exists(paths.log):
        if run_dirs or records or corrupt:
            problems.insert(0, "the run log is missing but evidence of earlier runs exists (runs: "
                               f"{run_dirs}; recovery records: {sorted(records) + corrupt}); use --stage recover-runs")
            raise RunControlError("run log reconciliation failed:\n  - " + "\n  - ".join(problems))
        return {"previous": [], "status": {}, "interrupted": []}

    data, lines = _read_lines(paths.log)
    if data and not data.endswith(b"\n"):
        problems.append("run log is truncated or was edited (no trailing newline)")
    parsed = _parse_lines(lines)
    anchor = max((i for i, e in enumerate(parsed) if e and e.get("event") == "recovery"), default=None)

    latest = None
    if records:
        seqs = [r[0]["seq"] for r in records.values()]
        if len(seqs) != len(set(seqs)):
            problems.append("two recovery records share a sequence number")
        latest = max(records.values(), key=lambda r: r[0]["seq"])
        R, R_sha, _ = latest
        a = parsed[anchor] if anchor is not None else None
        if a is None or a.get("recovery_id") != R["recovery_id"] or a.get("record_sha256") != R_sha:
            problems.append(f"latest recovery record {R['recovery_id']} is not matched by the last recovery entry in "
                            "the run log (the log, the entry or the record was lost or changed)")
        prior = R["prior_recoveries"]
        if sorted(p.get("seq") for p in prior) != list(range(1, R["seq"])):
            problems.append(f"recovery record {R['recovery_id']} does not list every earlier recovery")
        listed = set()
        for pr in prior:
            rid, want = pr.get("recovery_id"), pr.get("sha256")
            listed.add(rid)
            f = os.path.join(paths.recoveries, f"{rid}.json")
            if pr.get("status", "").startswith("present") and not os.path.exists(f):
                problems.append(f"acknowledged recovery record {rid} is missing")
            elif os.path.exists(f) and want and sha256_file(f) != want:
                problems.append(f"acknowledged recovery record {rid} was modified")
        for rid in records:
            if rid != R["recovery_id"] and rid not in listed:
                problems.append(f"recovery record {rid} is not acknowledged by the latest recovery record")
        prev_known = next((p.get("sha256") for p in prior if p.get("seq") == R["seq"] - 1), None)
        if R.get("prev_record_sha256") != prev_known:
            problems.append(f"recovery record {R['recovery_id']} has an inconsistent prev_record_sha256")
    elif anchor is not None:
        problems.append(f"run log recovery entry {parsed[anchor].get('recovery_id')} has no recovery record")

    acknowledged, known_without_dir = {}, []
    if anchor is not None:
        a = parsed[anchor]
        expect_prev = _sha_bytes(lines[anchor - 1]) if anchor else GENESIS
        if a.get("log_prefix_lines") != anchor or a.get("log_prefix_sha256") != _prefix_sha(lines[:anchor]) \
                or a.get("prev_sha256") != expect_prev:
            problems.append(f"run log recovery entry at line {anchor + 1} does not match the preserved log prefix")
        if latest is not None:
            R = latest[0]
            acknowledged = R["runs"]
            known_without_dir = sorted(R["runs_without_directory"])
            if R["log"].get("lines") != anchor or R["log"].get("prefix_sha256") != a.get("log_prefix_sha256"):
                problems.append(f"recovery record {R['recovery_id']} disagrees with its log entry about the log prefix")
            for rid, info in acknowledged.items():
                d = os.path.join(paths.runs, rid)
                if not os.path.isdir(d):
                    problems.append(f"acknowledged run {rid} is missing or changed since the recovery: directory missing")
                    continue
                diff = _inventory_diff(info.get("files", {}), _inventory(d))
                if any(diff.values()):
                    problems.append(f"acknowledged run {rid} is missing or changed since the recovery: {diff}")
        start, prev = anchor + 1, _sha_bytes(lines[anchor])
    else:
        start, prev = 0, GENESIS

    seg = []
    for n in range(start, len(lines)):
        if parsed[n] is None:
            problems.append(f"run log line {n + 1} is not valid JSON")
            break
        if parsed[n].get("prev_sha256") != prev:
            problems.append(f"run log hash chain broken at line {n + 1} (an entry was edited, removed, "
                            "duplicated or reordered)")
            break
        prev = _sha_bytes(lines[n])
        seg.append(parsed[n])

    previous = sorted(set(acknowledged) | set(known_without_dir))
    status = {r: "acknowledged" for r in previous}
    started, ended = {}, {}
    for e in seg:
        ev, rid = e.get("event"), e.get("run_id")
        if ev == "started":
            if rid in started or rid in status:
                problems.append(f"run {rid} started more than once")
                continue
            if not isinstance(rid, str) or not RUN_ID_RE.match(rid):
                problems.append(f"malformed run id in log: {rid!r}")
            if e.get("previous_runs") != previous:
                problems.append(f"run {rid} records previous runs {e.get('previous_runs')} but the log implies "
                                f"{previous}")
            started[rid] = e
            previous = previous + [rid]
            status[rid] = "started"
        elif ev in END_EVENTS:
            if rid not in started:
                problems.append(f"'{ev}' entry for run {rid} without a preceding 'started' entry")
            elif rid in ended:
                problems.append(f"run {rid} closed more than once")
            else:
                ended[rid] = e
                status[rid] = ev
        else:
            problems.append(f"unexpected run log event {ev!r} after the last recovery")

    for rid in run_dirs:
        if rid not in started and rid not in acknowledged:
            problems.append(f"orphaned run directory {rid} (no log entry)")
    for rid, e in started.items():
        d = os.path.join(paths.runs, rid)
        if not os.path.isdir(d):
            problems.append(f"run {rid} is in the log but its directory is missing")
            continue
        try:
            rj = json.load(open(os.path.join(d, "run.json"), encoding="utf-8"))
        except (OSError, ValueError):
            problems.append(f"run {rid}: run.json missing or corrupt")
            continue
        if rj != _strip(e):
            problems.append(f"run {rid}: run.json differs from its 'started' log entry")
        close_p, outs_p = os.path.join(d, "close.json"), os.path.join(d, "outputs_sha256.json")
        if rid in ended:
            try:
                cj = json.load(open(close_p, encoding="utf-8"))
                outs = json.load(open(outs_p, encoding="utf-8"))
            except (OSError, ValueError):
                problems.append(f"run {rid}: closed in the log but close.json/outputs_sha256.json missing or corrupt")
                continue
            if cj != _strip(ended[rid]) or cj.get("status") != ended[rid]["event"]:
                problems.append(f"run {rid}: close.json differs from its end log entry")
            if _json_sha(outs) != cj.get("outputs_sha256"):
                problems.append(f"run {rid}: outputs_sha256.json differs from the recorded outputs hash")
            extra = set(_inventory(d)) - set(outs) - {"close.json", "outputs_sha256.json"}
            if extra:
                problems.append(f"run {rid}: files added after closing: {sorted(extra)}")
            for rel, h in outs.items():
                p = os.path.join(d, rel)
                if not os.path.exists(p) or sha256_file(p) != h:
                    problems.append(f"run {rid}: output {rel} missing or modified")
        elif os.path.exists(close_p) or os.path.exists(outs_p):
            problems.append(f"run {rid}: closed on disk but the log has no end entry (log entries removed?)")
    if problems:
        raise RunControlError("run log reconciliation failed:\n  - " + "\n  - ".join(problems))
    interrupted = [r for r, st in status.items() if st == "started"]
    return {"previous": previous, "status": status, "interrupted": interrupted}


def _append_log(path, entry):
    """Append one entry chained to the last line (callers reconcile first)."""
    prev = GENESIS
    if os.path.exists(path):
        data, lines = _read_lines(path)
        if lines:
            prev = _sha_bytes(lines[-1])
    entry["prev_sha256"] = prev
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:  # append only
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


def _recovery_plan(paths):
    """Facts for a recovery, or RunControlError (fail closed) if the evidence is contradictory."""
    records, corrupt = _load_records(paths)
    if corrupt:
        raise RunControlError(f"recovery refused (fail closed): recovery record(s) {corrupt} cannot be read, so the "
                              "earlier acknowledgements cannot be interpreted. Restore them from version control.")
    seqs = {}
    for rid, (rec, _, _) in records.items():
        seqs.setdefault(rec["seq"], []).append(rid)
    dup = {k: v for k, v in seqs.items() if len(v) > 1}
    if dup:
        raise RunControlError(f"recovery refused (fail closed): conflicting recovery records share sequence numbers "
                              f"{dup}; choosing one would be an unsupported claim about the history.")
    log_missing = not os.path.exists(paths.log)
    data, lines = (b"", []) if log_missing else _read_lines(paths.log)
    parsed = _parse_lines(lines)
    # independent claims about each recovery record: from log entries and from other records
    claims = {}   # recovery_id -> {"seq": int, "hashes": {source: sha}}

    def claim(rid, seq, sha, source):
        c = claims.setdefault(rid, {"seq": seq, "hashes": {}})
        if seq is not None and c["seq"] is not None and c["seq"] != seq:
            raise RunControlError(f"recovery refused (fail closed): sources disagree about the sequence number of "
                                  f"recovery record {rid}.")
        c["seq"] = c["seq"] if c["seq"] is not None else seq
        if sha:
            c["hashes"][source] = sha
    for i, e in enumerate(parsed):
        if e and e.get("event") == "recovery":
            claim(e.get("recovery_id"), e.get("seq"), e.get("record_sha256"), f"log line {i + 1}")
    for rid, (rec, _, _) in records.items():
        claim(rid, rec["seq"], None, "file")
        for pr in rec["prior_recoveries"]:
            claim(pr.get("recovery_id"), pr.get("seq"), pr.get("sha256"), f"record {rid}")
    prior = []
    for rid, c in claims.items():
        known = set(c["hashes"].values())
        if len(known) > 1:
            raise RunControlError(f"recovery refused (fail closed): sources disagree about the hash of recovery "
                                  f"record {rid}: {c['hashes']}. Restore the original record from version control.")
        want = next(iter(known), None)
        if rid in records:
            have = records[rid][1]
            if want and have != want:
                raise RunControlError(f"recovery refused (fail closed): recovery record {rid} was modified (its bytes "
                                      f"differ from the hash recorded by {sorted(c['hashes'])}). Restore it from "
                                      "version control; acknowledging the modified record would be an unsupported claim.")
            prior.append({"seq": c["seq"], "recovery_id": rid, "sha256": have,
                          "status": "present_verified" if want else "present_unverifiable",
                          "hash_sources": sorted(c["hashes"])})
        else:
            prior.append({"seq": c["seq"], "recovery_id": rid, "sha256": want, "status": "missing",
                          "hash_sources": sorted(c["hashes"])})
    if any(p["seq"] is None for p in prior):
        raise RunControlError("recovery refused (fail closed): a recovery record is referenced without a sequence "
                              "number.")
    prior.sort(key=lambda p: p["seq"])
    seq = (prior[-1]["seq"] if prior else 0) + 1
    if [p["seq"] for p in prior] != list(range(1, seq)):
        missing_seqs = sorted(set(range(1, seq)) - {p["seq"] for p in prior})
        raise RunControlError(f"recovery refused (fail closed): recovery sequence numbers {missing_seqs} are not "
                              "evidenced by any surviving record or log entry; their existence cannot be "
                              "acknowledged without an unsupported claim.")
    return records, log_missing, data, lines, parsed, prior, seq


def recover(paths, authorised_by, reason, now=None):
    """Authorised, append-only acknowledgement of the surviving evidence (see the module docstring)."""
    if not str(authorised_by or "").strip() or not str(reason or "").strip():
        raise RunControlError("recovery requires --authorised-by and --recovery-reason")
    live = set(_OPEN_RUNS)
    try:
        state = reconcile(paths)
    except RunControlError as e:
        problems = str(e).split("\n  - ")[1:] or [str(e)]
    else:
        pending = [r for r in state["interrupted"] if r not in live]
        if not pending:
            raise RunControlError("run history reconciles and no interrupted run awaits acknowledgement; "
                                  "nothing to recover")
        problems = [f"interrupted run {r} (started, never closed) acknowledged; its outputs are protected from "
                    "this recovery onward" for r in pending]
    records, log_missing, data, lines, parsed, prior, seq = _recovery_plan(paths)
    latest = max(records.values(), key=lambda r: r[0]["seq"])[0] if records else None
    started_in_log = {e.get("run_id") for e in parsed if e and e.get("event") == "started"}
    ended_in_log = {e.get("run_id") for e in parsed if e and e.get("event") in END_EVENTS}
    dirs = sorted(d for d in (os.listdir(paths.runs) if os.path.isdir(paths.runs) else [])
                  if os.path.isdir(os.path.join(paths.runs, d)))
    runs = {}
    for rid in dirs:
        d = os.path.join(paths.runs, rid)
        inv = _inventory(d)
        on_disk = "closed" if "close.json" in inv else ("interrupted" if "run.json" in inv else "no_run_json")
        outputs = "unprotected before this recovery (interrupted run)" if on_disk == "interrupted" else "unverifiable"
        if on_disk == "closed":
            try:
                outs = json.load(open(os.path.join(d, "outputs_sha256.json"), encoding="utf-8"))
                ok = all(inv.get(k) == v for k, v in outs.items()) and \
                    not set(inv) - set(outs) - {"close.json", "outputs_sha256.json"}
                outputs = "consistent with its close record" if ok else "inconsistent with its close record"
            except (OSError, ValueError):
                outputs = "close record unreadable"
        before = (latest["runs"].get(rid) or {}).get("files") if latest else None
        runs[rid] = {"files": inv, "on_disk_state": on_disk, "outputs_at_recovery": outputs,
                     "log_entries": ("present" if rid in started_in_log else "missing"),
                     "log_end_entry": ("present" if rid in ended_in_log else "missing"),
                     "changed_since_previous_acknowledgement": (None if before is None else
                                                                _inventory_diff(before, inv))}
    without_dir = {}
    for rid in sorted(started_in_log - set(dirs) - {None}):
        without_dir[rid] = {"evidence": "log 'started' entry", "directory": "missing"}
    if latest:
        for rid in sorted((set(latest["runs"]) | set(latest["runs_without_directory"])) - set(dirs)):
            without_dir.setdefault(rid, {"evidence": f"recovery record {latest['recovery_id']}",
                                         "directory": "missing"})
    now = now or datetime.datetime.now(datetime.timezone.utc)
    rid = now.strftime("%Y%m%dT%H%M%SZ") + f"-r{seq:03d}-" + _json_sha([str(now), problems, sorted(runs)])[:8]
    record = {
        "schema": RECOVERY_SCHEMA, "recovery_id": rid, "seq": seq, "created_utc": now.isoformat(),
        "authorised_by": authorised_by, "reason": reason, "problems": problems,
        "prev_record_sha256": prior[-1]["sha256"] if prior else None, "prior_recoveries": prior,
        "log": {"missing": log_missing, "sha256": None if log_missing else _sha_bytes(data), "lines": len(lines),
                "prefix_sha256": _prefix_sha(lines), "had_trailing_newline": (not data) or data.endswith(b"\n")},
        "runs": runs, "runs_without_directory": without_dir,
        # C.1-compatible summary fields
        "log_missing": log_missing, "log_sha256_at_recovery": None if log_missing else _sha_bytes(data),
        "acknowledged_runs": {r: _json_sha(v["files"]) for r, v in runs.items()},
        "statement": ("This record acknowledges the evidence as found at this recovery. It does not restore, "
                      "reconstruct or vouch for missing log entries or records; file hashes protect the listed files "
                      "only from this recovery onward and do not establish their integrity before it."),
    }
    os.makedirs(paths.recoveries, exist_ok=True)
    rec_path = os.path.join(paths.recoveries, f"{rid}.json")
    with open(rec_path, "x", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, sort_keys=True)
    entry = {"event": "recovery", "recovery_id": rid, "seq": seq, "authorised_by": authorised_by, "reason": reason,
             "log_prefix_lines": len(lines), "log_prefix_sha256": record["log"]["prefix_sha256"],
             "record_sha256": sha256_file(rec_path), "prev_sha256": _sha_bytes(lines[-1]) if lines else GENESIS}
    os.makedirs(os.path.dirname(paths.log), exist_ok=True)
    with open(paths.log, "a", encoding="utf-8") as fh:  # append only; a missing last newline is completed
        if data and not data.endswith(b"\n"):
            fh.write("\n")
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
    reconcile(paths)  # every supported recovery must leave a reconciling state
    return record


# ------------------------------------------------------------------------------------------------ runs
_OPEN_RUNS = {}


class AuthorisedTestRun:
    """Handle of an open, authorised TEST run. Only `open_run` creates valid handles."""
    __test__ = False

    def __init__(self, run_id, run_dir, paths, manifest, start_record):
        self.run_id, self.run_dir, self.paths = run_id, run_dir, paths
        self.manifest, self.start_record = manifest, start_record
        self.exclusions_sha256 = manifest["evaluation_exclusions_sha256"]
        self.closed = False

    def verify(self):
        """Raise unless this is a live run opened by open_run and its inputs are still the frozen ones."""
        if _OPEN_RUNS.get(self.run_id) is not self or self.closed:
            raise RunControlError("not an open authorised TEST run (use run_all.py --stage evaluate)")
        verify_manifest(self.paths)
        with open(os.path.join(self.run_dir, "run.json"), encoding="utf-8") as fh:
            if json.load(fh) != self.start_record:
                raise RunControlError("run.json changed after the run was opened")
        if not any(e.get("event") == "started" and e.get("run_id") == self.run_id for e in _log_entries(self.paths)):
            raise RunControlError("run is not recorded in the run log")


def _log_entries(paths):
    out = []
    if os.path.exists(paths.log):
        for line in _read_lines(paths.log)[1]:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def require_run(run):
    if not isinstance(run, AuthorisedTestRun):
        raise RunControlError("TEST rows may only be scored inside an authorised TEST run "
                              "(run_all.py --stage evaluate --split test --authorised-by NAME)")
    run.verify()
    return run


def open_run(paths, authorised_by, rerun_reason=None, now=None):
    if not str(authorised_by or "").strip():
        raise RunControlError("--authorised-by is required for a TEST evaluation")
    man = verify_manifest(paths)
    gs = git_state(paths.code_root)
    if not gs["clean"]:
        raise RunControlError(f"git working tree is not clean; TEST evaluation refused: {gs['dirty_paths']}")
    if not os.path.exists(paths.tuning):
        raise RunControlError("DEV tuning record missing (run --stage tune first)")
    tuning_bytes = open(paths.tuning, "rb").read()
    tuning = json.loads(tuning_bytes)
    if tuning.get("split") != "dev":
        raise RunControlError("tuning record is not a DEV-only record")
    state = reconcile(paths)
    pending = [r for r in state["interrupted"] if r not in _OPEN_RUNS]
    if pending:
        raise RunControlError(f"interrupted TEST run(s) {pending} must be acknowledged with --stage recover-runs "
                              "before a new TEST run (this protects their outputs)")
    previous = state["previous"]
    if previous and not str(rerun_reason or "").strip():
        raise RunControlError(f"a TEST run already exists ({', '.join(previous)}); a rerun requires "
                              "--rerun-reason and --authorised-by")
    now = now or datetime.datetime.now(datetime.timezone.utc)
    ci = code_identity(paths.code_root)
    hashes = {"manifest_sha256": sha256_file(paths.manifest),
              "benchmark_files": man["files"],
              "config_sha256": man["config_sha256"],
              "review_treatments_sha256": man["review_treatments_sha256"],
              "evaluation_exclusions_sha256": man["evaluation_exclusions_sha256"],
              "tuning_record_sha256": _sha_bytes(tuning_bytes),
              "code_sha256": ci["sha256"]}
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{stamp}-" + _json_sha([stamp, hashes])[:8]
    os.makedirs(paths.runs, exist_ok=True)
    run_dir = os.path.join(paths.runs, run_id)
    try:
        os.mkdir(run_dir)  # fails if it exists: a run directory is never reused
    except FileExistsError:
        raise RunControlError(f"run directory already exists: {run_id}") from None
    record = {"run_id": run_id, "started_utc": now.isoformat(), "split": "test",
              "authorised_by": authorised_by, "rerun_reason": rerun_reason or None,
              "previous_runs": previous, "approved_by_at_freeze": man["approved_by"],
              "tuning_chosen": tuning.get("chosen"), "hashes": hashes,
              "code_files_sha256": ci["files"], "git_head": gs["commit"], "git_worktree_clean": gs["clean"],
              "frozen_git_commit": man["code_identity"]["git_commit"], "environment": environment()}
    with open(os.path.join(run_dir, "run.json"), "x", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, sort_keys=True)
    _append_log(paths.log, {"event": "started", **record})
    with open(os.path.join(run_dir, "run.json"), encoding="utf-8") as fh:
        run = AuthorisedTestRun(run_id, run_dir, paths, man, json.load(fh))
    _OPEN_RUNS[run_id] = run
    return run


def close_run(run, status="completed", error=None):
    """Close a run. The manifest is re-verified first; if it fails, the run is closed as 'aborted' (evidence
    preserved) and RunControlError is raised."""
    if _OPEN_RUNS.get(run.run_id) is not run or run.closed:
        raise RunControlError("run is not open")
    if status not in END_EVENTS:
        raise ValueError(f"status must be one of {END_EVENTS}")
    integrity, cause = None, None
    try:  # the integrity-check boundary: ANY failure here is a close-integrity failure
        verify_manifest(run.paths)
    except Exception as e:  # noqa: BLE001 - deliberately broad, but only around verification
        integrity, cause = f"{type(e).__name__}: {e}", e
        status = "aborted"
        error = (f"{error}; " if error else "") + f"manifest verification failed at close: {integrity}"
    outputs = {}
    for root, _, files in os.walk(run.run_dir):
        for f in sorted(files):
            p = os.path.join(root, f)
            outputs[os.path.relpath(p, run.run_dir)] = sha256_file(p)
    with open(os.path.join(run.run_dir, "outputs_sha256.json"), "x", encoding="utf-8") as fh:
        json.dump(outputs, fh, indent=2, sort_keys=True)
    close = {"run_id": run.run_id, "status": status, "error": error, "outputs_sha256": _json_sha(outputs),
             "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    with open(os.path.join(run.run_dir, "close.json"), "x", encoding="utf-8") as fh:
        json.dump(close, fh, indent=2, sort_keys=True)
    for root, _, files in os.walk(run.run_dir):
        for f in files:
            os.chmod(os.path.join(root, f), stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)  # read-only
    _append_log(run.paths.log, {"event": status, **close})
    run.closed = True
    del _OPEN_RUNS[run.run_id]
    if integrity:
        raise RunControlError(f"run {run.run_id} closed as aborted: {integrity}") from cause
    return outputs
