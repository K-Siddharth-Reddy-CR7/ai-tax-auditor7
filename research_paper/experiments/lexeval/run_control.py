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
out-of-order events; wrong previous-run references; malformed run IDs.

Recovery (`recover`): only when reconciliation fails, with --authorised-by and --recovery-reason. Nothing is
deleted, repaired or rewritten. A recovery record (results/run_recoveries/<id>.json) snapshots the problems, the
exact current log bytes (hash and line count) and the digest of every run directory, and a 'recovery' entry is
appended to the log (a new log is started only if the log is missing, and the record says so). Afterwards the
acknowledged evidence must stay byte-identical, the acknowledged runs count as earlier runs, and every later
entry is reconciled normally.

LIMITS: the hash chain has no secret key. Anyone able to rewrite every local file (log, run directories,
recovery records) consistently can produce an undetectable history; deleting ALL evidence is also undetectable
locally. These controls detect accidental and casual changes and make the sanctioned route the only one this
code accepts; they are not cryptographic proof. Git history and the authors' records are the external check.
"""
import datetime
import fnmatch
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
# (hashed separately), frontend.
CODE_IDENTITY_PATTERNS = [
    "research_paper/experiments/run_all.py",
    "research_paper/experiments/lexeval/*.py",
    "research_paper/experiments/requirements.txt",
    "backend/server.py",
    "backend/lexitax_v2/*.py",
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
def code_identity(code_root):
    files = {}
    for pat in CODE_IDENTITY_PATTERNS:
        for p in glob.glob(os.path.join(code_root, pat)):
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
    return any(fnmatch.fnmatchcase(path, pat) for pat in CODE_IDENTITY_PATTERNS)


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
    with open(paths.manifest, encoding="utf-8") as fh:
        man = json.load(fh)
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


def _dir_digest(d):
    files = {}
    for root, _, fs in os.walk(d):
        for f in fs:
            p = os.path.join(root, f)
            files[os.path.relpath(p, d)] = sha256_file(p)
    return _json_sha(files)


def _prefix_sha(lines):
    return _sha_bytes(b"".join(line + b"\n" for line in lines))


def _strip(e):
    return {k: v for k, v in e.items() if k not in ("event", "prev_sha256")}


def reconcile(paths):
    """Check that the log, run directories and recovery records agree. Returns
    {"previous": [run ids in order], "status": {run_id: started|completed|aborted|acknowledged}}; raises
    RunControlError listing every problem otherwise."""
    problems = []
    run_dirs = sorted(os.listdir(paths.runs)) if os.path.isdir(paths.runs) else []
    for d in run_dirs:
        if not os.path.isdir(os.path.join(paths.runs, d)):
            problems.append(f"unexpected file in runs/: {d}")
    run_dirs = [d for d in run_dirs if os.path.isdir(os.path.join(paths.runs, d))]
    rec_files = sorted(glob.glob(os.path.join(paths.recoveries, "*.json"))) if os.path.isdir(paths.recoveries) else []

    if not os.path.exists(paths.log):
        if run_dirs or rec_files:
            raise RunControlError("run log reconciliation failed:\n  - the run log is missing but evidence of "
                                  f"earlier runs exists (runs: {run_dirs}; recovery records: "
                                  f"{[os.path.basename(f) for f in rec_files]}); use --stage recover-runs")
        return {"previous": [], "status": {}}

    data, lines = _read_lines(paths.log)
    if data and not data.endswith(b"\n"):
        problems.append("run log is truncated or was edited (no trailing newline)")
    parsed = []
    for line in lines:
        try:
            parsed.append(json.loads(line))
        except json.JSONDecodeError:
            parsed.append(None)

    # the latest recovery entry anchors the log: earlier lines are acknowledged evidence, checked by hash only
    anchor, acknowledged, recoveries_in_log = None, {}, {}
    for i, e in enumerate(parsed):
        if isinstance(e, dict) and e.get("event") == "recovery":
            recoveries_in_log[e.get("recovery_id")] = e.get("record_sha256")
            anchor = i
    if anchor is not None:
        a = parsed[anchor]
        expect_prev = _sha_bytes(lines[anchor - 1]) if anchor else GENESIS
        if a.get("log_prefix_lines") != anchor or a.get("log_prefix_sha256") != _prefix_sha(lines[:anchor]) \
                or a.get("prev_sha256") != expect_prev:
            problems.append(f"run log recovery entry at line {anchor + 1} does not match the preserved log prefix")
        acknowledged = a.get("acknowledged_runs") or {}
        for rid, digest in acknowledged.items():
            d = os.path.join(paths.runs, rid)
            if not os.path.isdir(d) or _dir_digest(d) != digest:
                problems.append(f"acknowledged run {rid} is missing or changed since the recovery")
        start, prev = anchor + 1, _sha_bytes(lines[anchor])
    else:
        start, prev = 0, GENESIS
    for f in rec_files:
        rid = os.path.splitext(os.path.basename(f))[0]
        if recoveries_in_log.get(rid) != sha256_file(f):
            problems.append(f"recovery record {rid} is not matched by a recovery entry in the run log")

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

    previous, status, started, ended = sorted(acknowledged), {r: "acknowledged" for r in acknowledged}, {}, {}
    for e in seg:
        ev, rid = e.get("event"), e.get("run_id")
        if ev == "started":
            if rid in started or rid in acknowledged:
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
            problems.append(f"unknown run log event {ev!r}")

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
        except (OSError, json.JSONDecodeError):
            problems.append(f"run {rid}: run.json missing or corrupt")
            continue
        if rj != _strip(e):
            problems.append(f"run {rid}: run.json differs from its 'started' log entry")
        close_p, outs_p = os.path.join(d, "close.json"), os.path.join(d, "outputs_sha256.json")
        if rid in ended:
            try:
                cj = json.load(open(close_p, encoding="utf-8"))
                outs = json.load(open(outs_p, encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                problems.append(f"run {rid}: closed in the log but close.json/outputs_sha256.json missing or corrupt")
                continue
            if cj != _strip(ended[rid]) or cj.get("status") != ended[rid]["event"]:
                problems.append(f"run {rid}: close.json differs from its end log entry")
            if _json_sha(outs) != cj.get("outputs_sha256"):
                problems.append(f"run {rid}: outputs_sha256.json differs from the recorded outputs hash")
            present = {os.path.relpath(os.path.join(r, f), d) for r, _, fs in os.walk(d) for f in fs}
            if present - set(outs) - {"close.json", "outputs_sha256.json"}:
                problems.append(f"run {rid}: files added after closing: {sorted(present - set(outs) - {'close.json', 'outputs_sha256.json'})}")
            for rel, h in outs.items():
                p = os.path.join(d, rel)
                if not os.path.exists(p) or sha256_file(p) != h:
                    problems.append(f"run {rid}: output {rel} missing or modified")
        elif os.path.exists(close_p) or os.path.exists(outs_p):
            problems.append(f"run {rid}: closed on disk but the log has no end entry (log entries removed?)")
    if problems:
        raise RunControlError("run log reconciliation failed:\n  - " + "\n  - ".join(problems))
    return {"previous": previous, "status": status}


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


def recover(paths, authorised_by, reason, now=None):
    """Authorised, evidence-preserving acknowledgement of an inconsistent run history (see module docstring)."""
    if not str(authorised_by or "").strip() or not str(reason or "").strip():
        raise RunControlError("recovery requires --authorised-by and --recovery-reason")
    try:
        reconcile(paths)
    except RunControlError as e:
        problems = str(e).split("\n  - ")[1:] or [str(e)]
    else:
        raise RunControlError("run history reconciles; nothing to recover")
    now = now or datetime.datetime.now(datetime.timezone.utc)
    log_missing = not os.path.exists(paths.log)
    data, lines = (b"", []) if log_missing else _read_lines(paths.log)
    acknowledged = {d: _dir_digest(os.path.join(paths.runs, d)) for d in
                    (sorted(os.listdir(paths.runs)) if os.path.isdir(paths.runs) else [])
                    if os.path.isdir(os.path.join(paths.runs, d))}
    rid = now.strftime("%Y%m%dT%H%M%SZ") + "-" + _json_sha([str(now), problems, acknowledged])[:8]
    record = {"recovery_id": rid, "created_utc": now.isoformat(), "authorised_by": authorised_by,
              "reason": reason, "problems": problems, "log_missing": log_missing,
              "log_sha256_at_recovery": None if log_missing else _sha_bytes(data),
              "log_had_trailing_newline": (not data) or data.endswith(b"\n"),
              "log_prefix_lines": len(lines), "log_prefix_sha256": _prefix_sha(lines),
              "acknowledged_runs": acknowledged}
    os.makedirs(paths.recoveries, exist_ok=True)
    rec_path = os.path.join(paths.recoveries, f"{rid}.json")
    with open(rec_path, "x", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, sort_keys=True)
    entry = {"event": "recovery", "recovery_id": rid, "authorised_by": authorised_by, "reason": reason,
             "log_prefix_lines": len(lines), "log_prefix_sha256": record["log_prefix_sha256"],
             "acknowledged_runs": acknowledged, "record_sha256": sha256_file(rec_path),
             "prev_sha256": _sha_bytes(lines[-1]) if lines else GENESIS}
    os.makedirs(os.path.dirname(paths.log), exist_ok=True)
    with open(paths.log, "a", encoding="utf-8") as fh:  # append only; a missing last newline is completed
        if data and not data.endswith(b"\n"):
            fh.write("\n")
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
    reconcile(paths)
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
    integrity = None
    try:
        verify_manifest(run.paths)
    except RunControlError as e:
        integrity = str(e)
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
        raise RunControlError(f"run {run.run_id} closed as aborted: {integrity}")
    return outputs
