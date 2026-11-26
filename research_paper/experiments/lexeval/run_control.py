"""Phase C (IMPLEMENTATION_PLAN.md): permanent TEST run controls.

An authorised TEST evaluation is the only way TEST rows may be scored. `open_run()`:
  1. verifies the frozen manifest: benchmark files, excluded_items.csv, config, review-treatments file and
     evaluation-exclusions file must all match their recorded SHA-256 (nothing is taken from the caller);
  2. requires the DEV tuning record (results/tuning_dev.json, split "dev");
  3. verifies the append-only, hash-chained run log (results/test_runs.jsonl);
  4. requires --authorised-by for every run, and additionally --rerun-reason if any run was started before;
  5. creates a new permanent run directory results/runs/<run_id>/ (never reused or overwritten) and appends a
     'started' entry recording all input and code hashes.
`close_run()` records the SHA-256 of every output, makes the outputs read-only and appends a 'completed' or
'aborted' entry. Earlier runs and log entries are never modified.

Limits: Python cannot stop deliberately written code from re-implementing the evaluation. These controls make
the sanctioned route (`run_all.py --stage evaluate`) the only one the evaluation code accepts, and they make
any extra run visible in the log.
"""
import datetime
import glob
import hashlib
import json
import os
import stat
import subprocess

from .paths import EXP, GEN, PILOT, REPO, RESULTS

DATA_FILES = ["product_benchmark.csv", "country_benchmark.csv", "malformed_inputs.csv"]
EXCLUDED_FILE = "excluded_items.csv"
GENESIS = "0" * 64


class RunControlError(RuntimeError):
    """A TEST run was refused (manifest, tuning record, log, authorisation or run directory problem)."""


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

    def as_dict(self):
        return {k: v for k, v in vars(self).items()}


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def verify_manifest(paths):
    """Return the manifest if every recorded hash matches the current files; otherwise raise."""
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
    if problems:
        raise RunControlError("manifest verification failed:\n  - " + "\n  - ".join(problems))
    return man


def code_hashes(code_root):
    rels = ["research_paper/experiments/run_all.py", "backend/server.py"]
    rels += sorted(os.path.relpath(p, code_root) for p in
                   glob.glob(os.path.join(code_root, "research_paper/experiments/lexeval/*.py"))
                   + glob.glob(os.path.join(code_root, "backend/lexitax_v2/*.py")))
    per = {r: sha256_file(os.path.join(code_root, r)) for r in rels if os.path.exists(os.path.join(code_root, r))}
    combined = hashlib.sha256("".join(f"{k}={v}\n" for k, v in sorted(per.items())).encode()).hexdigest()
    return per, combined


def _git(code_root, *args):
    try:
        return subprocess.run(["git", "-C", code_root, *args], capture_output=True, text=True, timeout=10,
                              check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def read_log(path):
    """Parse and verify the hash chain of the append-only run log. Returns the list of entries."""
    if not os.path.exists(path):
        return []
    with open(path, "rb") as fh:
        data = fh.read()
    if data and not data.endswith(b"\n"):
        raise RunControlError("run log is truncated or was edited (no trailing newline)")
    entries, prev = [], GENESIS
    for n, line in enumerate(data.splitlines(), 1):
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            raise RunControlError(f"run log line {n} is not valid JSON") from None
        if e.get("prev_sha256") != prev:
            raise RunControlError(f"run log hash chain broken at line {n} (an entry was edited or removed)")
        prev = hashlib.sha256(line).hexdigest()
        entries.append(e)
    return entries


def _append_log(path, entry):
    entries = read_log(path)
    if entries:
        with open(path, "rb") as fh:
            last = fh.read().splitlines()[-1]
        entry["prev_sha256"] = hashlib.sha256(last).hexdigest()
    else:
        entry["prev_sha256"] = GENESIS
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:  # append only
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


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
        if not any(e.get("event") == "started" and e.get("run_id") == self.run_id for e in read_log(self.paths.log)):
            raise RunControlError("run is not recorded in the run log")


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
    if not os.path.exists(paths.tuning):
        raise RunControlError("DEV tuning record missing (run --stage tune first)")
    with open(paths.tuning, encoding="utf-8") as fh:
        tuning = json.load(fh)
    if tuning.get("split") != "dev":
        raise RunControlError("tuning record is not a DEV-only record")
    log = read_log(paths.log)
    previous = [e["run_id"] for e in log if e.get("event") == "started"]
    if previous and not str(rerun_reason or "").strip():
        raise RunControlError(f"a TEST run already exists ({', '.join(previous)}); a rerun requires "
                              "--rerun-reason and --authorised-by")
    now = now or datetime.datetime.now(datetime.timezone.utc)
    per_file, code_sha = code_hashes(paths.code_root)
    hashes = {"manifest_sha256": sha256_file(paths.manifest),
              "benchmark_files": man["files"],
              "config_sha256": man["config_sha256"],
              "review_treatments_sha256": man["review_treatments_sha256"],
              "evaluation_exclusions_sha256": man["evaluation_exclusions_sha256"],
              "tuning_record_sha256": sha256_file(paths.tuning),
              "code_sha256": code_sha}
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{stamp}-" + hashlib.sha256(json.dumps([stamp, hashes], sort_keys=True).encode()).hexdigest()[:8]
    os.makedirs(paths.runs, exist_ok=True)
    run_dir = os.path.join(paths.runs, run_id)
    try:
        os.mkdir(run_dir)  # fails if it exists: a run directory is never reused
    except FileExistsError:
        raise RunControlError(f"run directory already exists: {run_id}") from None
    record = {"run_id": run_id, "started_utc": now.isoformat(), "split": "test",
              "authorised_by": authorised_by, "rerun_reason": rerun_reason or None,
              "previous_runs": previous, "approved_by_at_freeze": man["approved_by"],
              "tuning_chosen": tuning.get("chosen"), "hashes": hashes, "code_files_sha256": per_file,
              "git_head": _git(paths.code_root, "rev-parse", "HEAD"),
              "git_worktree_clean": _git(paths.code_root, "status", "--porcelain") == ""}
    with open(os.path.join(run_dir, "run.json"), "x", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, sort_keys=True)
    _append_log(paths.log, {"event": "started", **record})
    run = AuthorisedTestRun(run_id, run_dir, paths, man, json.load(open(os.path.join(run_dir, "run.json"))))
    _OPEN_RUNS[run_id] = run
    return run


def close_run(run, status="completed", error=None):
    if _OPEN_RUNS.get(run.run_id) is not run or run.closed:
        raise RunControlError("run is not open")
    outputs = {}
    for root, _, files in os.walk(run.run_dir):
        for f in sorted(files):
            p = os.path.join(root, f)
            outputs[os.path.relpath(p, run.run_dir)] = sha256_file(p)
    with open(os.path.join(run.run_dir, "outputs_sha256.json"), "x", encoding="utf-8") as fh:
        json.dump(outputs, fh, indent=2, sort_keys=True)
    for root, _, files in os.walk(run.run_dir):
        for f in files:
            p = os.path.join(root, f)
            os.chmod(p, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)  # read-only: never silently replaced
    _append_log(run.paths.log, {"event": status, "run_id": run.run_id,
                                "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                "outputs_sha256": hashlib.sha256(json.dumps(outputs, sort_keys=True).encode()).hexdigest(),
                                "error": error})
    run.closed = True
    del _OPEN_RUNS[run.run_id]
    return outputs
