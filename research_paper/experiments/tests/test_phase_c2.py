"""Phase C.2: repeated, evidence-preserving recovery (D2), close-time integrity failures (D3), protection of
interrupted-run outputs (D4), and nested-module code identity (D5).

Temporary fixtures only: synthetic benchmarks, synthetic manifests, temporary git repositories and run
directories. Nothing is written to the real results/ directory and no real manifest is created.
"""
import datetime
import hashlib
import json
import os
import shutil
import stat

import pytest
from _runfix import git, make_paths
from test_eval_exclusions import syn  # noqa: F401  (fixture)

import run_all
from lexeval import evaluate, run_control
from lexeval.paths import GEN, RESULTS
from lexeval.run_control import (RunControlError, close_run, code_identity, manifest_record, open_run, reconcile,
                                 recover)
from lexeval.systems import primary_systems

T0 = datetime.datetime(2026, 12, 2, 9, 0, 0, tzinfo=datetime.timezone.utc)


def _at(n):
    return T0 + datetime.timedelta(minutes=n)


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def _tree(d):
    out = {}
    for root, _, fs in os.walk(d):
        for f in fs:
            out[os.path.relpath(os.path.join(root, f), d)] = _sha(os.path.join(root, f))
    return out


@pytest.fixture(autouse=True)
def _real_state_untouched():
    man = os.path.join(GEN, "MANIFEST.json")
    before = (_tree(RESULTS) if os.path.exists(RESULTS) else None, os.path.exists(man) and _sha(man))
    yield
    assert (_tree(RESULTS) if os.path.exists(RESULTS) else None, os.path.exists(man) and _sha(man)) == before


@pytest.fixture
def paths(syn, tmp_path):
    return make_paths(tmp_path, syn["gen"], syn["path"], syn["pilot"])


class Clock:
    def __init__(self):
        self.n = 0

    def __call__(self):
        self.n += 1
        return _at(self.n)


@pytest.fixture
def clock():
    return Clock()


def _run(paths, clock, interrupted=False, evaluate_outputs=False):
    prev = reconcile(paths)["previous"]
    r = open_run(paths, "synthetic test", rerun_reason="next run" if prev else None, now=clock())
    if evaluate_outputs:
        evaluate.evaluate(primary_systems(), "test", "primary", run=r)
    if interrupted:
        run_control._OPEN_RUNS.pop(r.run_id)     # simulates a crash before close
    else:
        close_run(r)
    return r


def _recover(paths, clock, why="test recovery"):
    return recover(paths, "author one", why, now=clock())


def _lines(paths):
    return open(paths.log, "rb").read().splitlines(keepends=True)


def _write_lines(paths, lines):
    open(paths.log, "wb").write(b"".join(lines))


def _records(paths):
    d = paths.recoveries
    return {f: _sha(os.path.join(d, f)) for f in sorted(os.listdir(d))} if os.path.isdir(d) else {}


def _writable(p):
    os.chmod(p, stat.S_IWUSR | stat.S_IRUSR)


def _evidence(paths):
    """Every surviving evidence file (run directories, recovery records) with hashes."""
    return {"runs": _tree(paths.runs) if os.path.isdir(paths.runs) else {}, "records": _records(paths)}


def _preserved(before, after):
    """Every file present before is still present and byte-identical."""
    for k in ("runs", "records"):
        for f, h in before[k].items():
            assert after[k].get(f) == h, f"{k}/{f} changed or disappeared"


# ============================================================================ D2: repeated recovery
def test_initial_recovery_after_log_deletion(paths, clock):
    a, b = _run(paths, clock), _run(paths, clock)
    ev = _evidence(paths)
    os.remove(paths.log)
    rec = _recover(paths, clock, "log deleted")
    assert rec["seq"] == 1 and rec["prior_recoveries"] == [] and rec["log"]["missing"] is True
    assert set(rec["runs"]) == {a.run_id, b.run_id}
    assert all(v["log_entries"] == "missing" and v["on_disk_state"] == "closed" for v in rec["runs"].values())
    assert all(v["outputs_at_recovery"] == "consistent with its close record" for v in rec["runs"].values())
    lines = _lines(paths)
    assert len(lines) == 1 and json.loads(lines[0])["event"] == "recovery"   # nothing reconstructed
    assert "does not restore" in rec["statement"]
    _preserved(ev, _evidence(paths))
    assert reconcile(paths)["previous"] == sorted([a.run_id, b.run_id])


def test_second_log_deletion_after_successful_recovery(paths, clock):
    a = _run(paths, clock)
    os.remove(paths.log)
    r1 = _recover(paths, clock, "first loss")
    c = _run(paths, clock)
    ev = _evidence(paths)
    os.remove(paths.log)
    with pytest.raises(RunControlError, match="log is missing"):
        reconcile(paths)
    r2 = _recover(paths, clock, "second loss")
    assert r2["seq"] == 2 and r2["prev_record_sha256"] == ev["records"][f"{r1['recovery_id']}.json"]
    assert r2["prior_recoveries"] == [{"seq": 1, "recovery_id": r1["recovery_id"],
                                       "sha256": ev["records"][f"{r1['recovery_id']}.json"],
                                       "status": "present_unverifiable", "hash_sources": []}]
    assert set(r2["runs"]) == {a.run_id, c.run_id}
    _preserved(ev, _evidence(paths))
    st = reconcile(paths)
    assert st["previous"] == sorted([a.run_id, c.run_id])
    _run(paths, clock)
    reconcile(paths)


def test_removal_of_first_recovery_entry(paths, clock):
    _run(paths, clock)
    _write_lines(paths, _lines(paths)[:-1])          # completed entry lost
    r1 = _recover(paths, clock, "entry lost")
    _run(paths, clock)
    lines = _lines(paths)
    idx = next(i for i, l in enumerate(lines) if json.loads(l)["event"] == "recovery")
    _write_lines(paths, lines[:idx] + lines[idx + 1:])   # the recovery entry itself removed
    with pytest.raises(RunControlError):
        reconcile(paths)
    ev = _evidence(paths)
    r2 = _recover(paths, clock, "recovery entry lost")
    assert [p["status"] for p in r2["prior_recoveries"]] == ["present_unverifiable"]
    assert r2["prior_recoveries"][0]["recovery_id"] == r1["recovery_id"]
    _preserved(ev, _evidence(paths))
    reconcile(paths)


def test_multiple_successive_recoveries_always_reconcile(paths, clock):
    damage = ["delete_log", "truncate_tail", "delete_log", "remove_recovery_entry", "orphan_dir", "delete_log"]
    history = []
    for n, what in enumerate(damage, 1):
        _run(paths, clock)
        if what == "delete_log":
            os.remove(paths.log)
        elif what == "truncate_tail":
            _write_lines(paths, _lines(paths)[:-1])
        elif what == "remove_recovery_entry":
            lines = _lines(paths)
            idx = max(i for i, l in enumerate(lines) if json.loads(l)["event"] == "recovery")
            _write_lines(paths, lines[:idx] + lines[idx + 1:])
        elif what == "orphan_dir":
            os.mkdir(os.path.join(paths.runs, f"20261202T23{n:02d}00Z-abcdef{n:02d}"))
        ev = _evidence(paths)
        rec = _recover(paths, clock, f"damage {n}: {what}")
        history.append(rec["recovery_id"])
        assert rec["seq"] == n and [p["seq"] for p in rec["prior_recoveries"]] == list(range(1, n))
        _preserved(ev, _evidence(paths))
        reconcile(paths)
    assert len(_records(paths)) == len(damage)
    _run(paths, clock)
    reconcile(paths)


def test_recovery_record_tampering_fails_closed(paths, clock):
    _run(paths, clock)
    os.remove(paths.log)
    r1 = _recover(paths, clock)
    p = os.path.join(paths.recoveries, f"{r1['recovery_id']}.json")
    original = open(p, "rb").read()
    _writable(p)
    open(p, "wb").write(original.replace(b"author one", b"someone else"))
    with pytest.raises(RunControlError, match="recovery record"):
        reconcile(paths)
    before = (_records(paths), open(paths.log, "rb").read())
    with pytest.raises(RunControlError, match="fail closed.*modified"):
        _recover(paths, clock, "after tampering")
    assert (_records(paths), open(paths.log, "rb").read()) == before    # nothing written
    open(p, "wb").write(original)                                         # restored from version control
    reconcile(paths)


def test_tampered_earlier_record_contradicted_by_later_record_fails_closed(paths, clock):
    _run(paths, clock)
    os.remove(paths.log)
    r1 = _recover(paths, clock)
    os.remove(paths.log)
    _recover(paths, clock)                    # record 2 lists record 1 with its hash
    p = os.path.join(paths.recoveries, f"{r1['recovery_id']}.json")
    _writable(p)
    with open(p, "a") as fh:
        fh.write(" ")
    with pytest.raises(RunControlError, match="acknowledged recovery record .* was modified"):
        reconcile(paths)
    with pytest.raises(RunControlError, match="fail closed"):
        _recover(paths, clock)


def test_missing_recovery_record_is_acknowledged_as_missing(paths, clock):
    _run(paths, clock)
    _write_lines(paths, _lines(paths)[:-1])
    r1 = _recover(paths, clock)
    sha1 = _records(paths)[f"{r1['recovery_id']}.json"]
    os.remove(os.path.join(paths.recoveries, f"{r1['recovery_id']}.json"))
    with pytest.raises(RunControlError, match="has no recovery record"):
        reconcile(paths)
    r2 = _recover(paths, clock, "record 1 lost")
    assert r2["prior_recoveries"] == [{"seq": 1, "recovery_id": r1["recovery_id"], "sha256": sha1,
                                       "status": "missing", "hash_sources": ["log line 2"]}]   # 'started' + recovery entry
    assert not os.path.exists(os.path.join(paths.recoveries, f"{r1['recovery_id']}.json"))   # not recreated
    reconcile(paths)


def test_missing_earlier_record_known_only_from_a_later_record(paths, clock):
    _run(paths, clock)
    os.remove(paths.log)
    r1 = _recover(paths, clock)
    os.remove(paths.log)
    _recover(paths, clock)
    os.remove(os.path.join(paths.recoveries, f"{r1['recovery_id']}.json"))
    with pytest.raises(RunControlError, match=f"acknowledged recovery record {r1['recovery_id']} is missing"):
        reconcile(paths)
    r3 = _recover(paths, clock)
    assert [(p["seq"], p["status"]) for p in r3["prior_recoveries"]] == [(1, "missing"), (2, "present_verified")]
    reconcile(paths)


@pytest.mark.parametrize("damage", ["invalid_json", "wrong_schema", "renamed"])
def test_corrupted_recovery_record_fails_closed(paths, clock, damage):
    _run(paths, clock)
    os.remove(paths.log)
    r1 = _recover(paths, clock)
    p = os.path.join(paths.recoveries, f"{r1['recovery_id']}.json")
    _writable(p)
    if damage == "invalid_json":
        open(p, "w").write("{broken")
    elif damage == "wrong_schema":
        rec = json.load(open(p))
        rec["schema"] = "something-else"
        json.dump(rec, open(p, "w"))
    else:
        os.rename(p, os.path.join(paths.recoveries, "other-name.json"))
    with pytest.raises(RunControlError, match="corrupt or unreadable"):
        reconcile(paths)
    before = (_records(paths), open(paths.log, "rb").read())
    with pytest.raises(RunControlError, match="fail closed.*cannot be read"):
        _recover(paths, clock)
    assert (_records(paths), open(paths.log, "rb").read()) == before


def test_duplicate_sequence_numbers_fail_closed(paths, clock):
    _run(paths, clock)
    os.remove(paths.log)
    r1 = _recover(paths, clock)
    rec = json.load(open(os.path.join(paths.recoveries, f"{r1['recovery_id']}.json")))
    rec["recovery_id"] = "20261202T000000Z-r001-forged00"
    json.dump(rec, open(os.path.join(paths.recoveries, rec["recovery_id"] + ".json"), "w"))
    with pytest.raises(RunControlError, match="share a sequence number"):
        reconcile(paths)
    with pytest.raises(RunControlError, match="fail closed.*share sequence numbers"):
        _recover(paths, clock)


def test_unevidenced_sequence_gap_fails_closed(paths, clock):
    _run(paths, clock)
    for _ in range(3):
        os.remove(paths.log)
        last = _recover(paths, clock)
    os.remove(paths.log)
    p = os.path.join(paths.recoveries, f"{last['recovery_id']}.json")   # seq 3, now unverifiable
    rec = json.load(open(p))
    for r in rec["prior_recoveries"]:
        os.remove(os.path.join(paths.recoveries, f"{r['recovery_id']}.json"))
    rec["prior_recoveries"] = []                    # tampered: earlier sequence numbers no longer evidenced
    _writable(p)
    json.dump(rec, open(p, "w"))
    with pytest.raises(RunControlError, match="fail closed.*sequence numbers \\[1, 2\\]"):
        _recover(paths, clock)


def test_acknowledged_history_is_classified_not_reconstructed(paths, clock):
    a, b, c = _run(paths, clock), _run(paths, clock), _run(paths, clock)
    shutil.rmtree(b.run_dir)                          # directory lost, log entries survive
    _write_lines(paths, _lines(paths)[:-2])           # c's log entries lost, directory survives
    rec = _recover(paths, clock)
    assert rec["runs"][a.run_id]["log_entries"] == "present"
    assert rec["runs"][c.run_id]["log_entries"] == "missing"
    assert rec["runs_without_directory"] == {b.run_id: {"evidence": "log 'started' entry", "directory": "missing"}}
    st = reconcile(paths)
    assert set(st["previous"]) == {a.run_id, b.run_id, c.run_id}
    events = [json.loads(l)["event"] for l in _lines(paths)]
    assert events.count("started") == 2 and events[-1] == "recovery"   # only the original surviving entries


def test_run_known_only_from_an_earlier_record_stays_in_history(paths, clock):
    a = _run(paths, clock)
    os.remove(paths.log)
    _recover(paths, clock)
    os.chmod(a.run_dir, stat.S_IRWXU)
    shutil.rmtree(a.run_dir)
    with pytest.raises(RunControlError, match="directory missing"):
        reconcile(paths)
    r2 = _recover(paths, clock)
    assert a.run_id in r2["runs_without_directory"] and a.run_id in reconcile(paths)["previous"]


def test_no_new_record_when_nothing_to_recover(paths, clock):
    _run(paths, clock)
    with pytest.raises(RunControlError, match="nothing to recover"):
        _recover(paths, clock)
    assert _records(paths) == {}


# ============================================================================ D3: close-time failures
@pytest.mark.parametrize("damage,cause", [("malformed_json", "JSONDecodeError"), ("missing", "RunControlError"),
                                          ("code_identity", "RunControlError"), ("benchmark", "RunControlError")])
def test_close_integrity_failures_record_aborted_and_keep_evidence(paths, clock, damage, cause):
    run = open_run(paths, "synthetic test", now=clock())
    evaluate.evaluate(primary_systems(), "test", "primary", run=run)
    if damage == "malformed_json":
        open(paths.manifest, "w").write("{not json")
    elif damage == "missing":
        os.remove(paths.manifest)
    elif damage == "code_identity":
        with open(os.path.join(paths.code_root, "backend/server.py"), "a") as fh:
            fh.write("\n# changed during the run\n")
        git(paths.code_root, "commit", "-qam", "change")
    else:
        open(os.path.join(paths.gen, "country_benchmark.csv"), "a").write("\n")
    with pytest.raises(RunControlError, match="closed as aborted") as ei:
        close_run(run)
    assert ei.value.__cause__ is not None
    if damage == "malformed_json":
        assert isinstance(ei.value.__cause__.__cause__, json.JSONDecodeError)   # original error preserved
    close = json.load(open(os.path.join(run.run_dir, "close.json")))
    assert close["status"] == "aborted" and "manifest verification failed at close" in close["error"]
    assert json.loads(_lines(paths)[-1])["event"] == "aborted"
    assert os.path.exists(os.path.join(run.run_dir, "processed", "primary_test_product_summary.csv"))
    reconcile(paths)                                   # evidence consistent, run counted as aborted


def test_stage_evaluate_keeps_the_original_error_when_close_also_fails(paths, monkeypatch):
    def failing_evaluation(*a, **k):
        open(paths.manifest, "w").write("{not json")   # integrity also broken before close
        raise ValueError("synthetic evaluation failure")
    monkeypatch.setattr(evaluate, "evaluate", failing_evaluation)
    with pytest.raises(ValueError, match="synthetic evaluation failure") as ei:
        run_all.stage_evaluate({}, "test", "synthetic test", paths=paths)
    assert any("close-time integrity check failed" in n for n in getattr(ei.value, "__notes__", []))
    last = json.loads(_lines(paths)[-1])
    assert last["event"] == "aborted"
    assert "evaluation failed: ValueError: synthetic evaluation failure" in last["error"]
    assert "manifest verification failed at close" in last["error"]


def test_stage_evaluate_close_failure_after_successful_evaluation_is_not_a_success(paths, monkeypatch):
    real_close = run_control.close_run

    def corrupt_then_close(run, status="completed", error=None):
        open(paths.manifest, "w").write("{not json")
        return real_close(run, status, error)
    monkeypatch.setattr(run_control, "close_run", corrupt_then_close)
    with pytest.raises(SystemExit, match="closed as aborted"):
        run_all.stage_evaluate({}, "test", "synthetic test", paths=paths)
    assert json.loads(_lines(paths)[-1])["event"] == "aborted"


def test_programming_errors_outside_the_verification_boundary_are_not_swallowed(paths, monkeypatch, clock):
    run = open_run(paths, "synthetic test", now=clock())
    monkeypatch.setattr(run_control.os, "chmod", lambda *a, **k: (_ for _ in ()).throw(TypeError("bug")))
    with pytest.raises(TypeError, match="bug"):
        close_run(run)


# ============================================================================ D4: interrupted-run outputs
def test_unchanged_interrupted_outputs_are_protected_after_recovery(paths, clock):
    r = _run(paths, clock, interrupted=True, evaluate_outputs=True)
    with pytest.raises(RunControlError, match="must be acknowledged"):
        open_run(paths, "synthetic test", rerun_reason="x", now=clock())
    rec = _recover(paths, clock, "interrupted run")
    info = rec["runs"][r.run_id]
    assert info["on_disk_state"] == "interrupted"
    assert info["outputs_at_recovery"] == "unprotected before this recovery (interrupted run)"
    assert info["files"] == _tree(r.run_dir) and "processed/primary_test_product_summary.csv" in info["files"]
    assert "do not establish their integrity before it" in rec["statement"]
    reconcile(paths)
    _run(paths, clock)


@pytest.mark.parametrize("change", ["modified", "deleted", "added"])
def test_interrupted_outputs_changed_after_recovery_are_detected(paths, clock, change):
    r = _run(paths, clock, interrupted=True, evaluate_outputs=True)
    _recover(paths, clock)
    p = os.path.join(r.run_dir, "processed", "primary_test_product_summary.csv")
    if change == "modified":
        with open(p, "a") as fh:
            fh.write("tampered\n")
    elif change == "deleted":
        os.remove(p)
    else:
        open(os.path.join(r.run_dir, "processed", "late.csv"), "w").write("x")
    with pytest.raises(RunControlError, match=f"'{change}': \\[[^\\]]*(primary_test_product_summary|late)"):
        reconcile(paths)


def test_interrupted_run_without_outputs(paths, clock):
    r = _run(paths, clock, interrupted=True)
    rec = _recover(paths, clock)
    assert set(rec["runs"][r.run_id]["files"]) == {"run.json"}
    reconcile(paths)


def test_repeated_recovery_of_acknowledged_interrupted_run(paths, clock):
    r = _run(paths, clock, interrupted=True, evaluate_outputs=True)
    r1 = _recover(paths, clock)
    os.remove(paths.log)
    r2 = _recover(paths, clock, "log lost after acknowledging the interrupted run")
    assert r2["runs"][r.run_id]["files"] == r1["runs"][r.run_id]["files"]
    assert r2["runs"][r.run_id]["changed_since_previous_acknowledgement"] == {"modified": [], "deleted": [], "added": []}
    reconcile(paths)
    with open(os.path.join(r.run_dir, "processed", "primary_test_product_summary.csv"), "a") as fh:
        fh.write("x\n")
    with pytest.raises(RunControlError, match="changed since the recovery"):
        reconcile(paths)
    r3 = _recover(paths, clock, "change acknowledged, not hidden")
    assert r3["runs"][r.run_id]["changed_since_previous_acknowledgement"]["modified"] == [
        "processed/primary_test_product_summary.csv"]
    assert open(os.path.join(paths.recoveries, f"{r1['recovery_id']}.json"), "rb").read()   # earlier record kept
    reconcile(paths)


# ============================================================================ D5: nested modules
def _commit(repo, msg="change"):
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", msg)


NESTED = "research_paper/experiments/lexeval/subpkg/helper.py"


def test_nested_module_is_part_of_code_identity(paths):
    os.makedirs(os.path.join(paths.code_root, os.path.dirname(NESTED)), exist_ok=True)
    open(os.path.join(paths.code_root, NESTED), "w").write("X = 1\n")
    assert NESTED in code_identity(paths.code_root)["files"]
    for f in code_identity(paths.code_root)["files"]:
        assert run_control._matches_identity(f)
    for f in ("research_paper/experiments/tests/test_x.py", "README.md", "research_paper/experiments/lexeval/x.pyc",
              "frontend/src/App.jsx", "research_paper/experiments/results/x.py"):
        assert not run_control._matches_identity(f)


@pytest.mark.parametrize("change", ["added", "modified", "deleted"])
def test_nested_module_changes_are_refused(paths, clock, change):
    repo = paths.code_root
    full = os.path.join(repo, NESTED)
    if change != "added":                              # nested module present at freeze
        os.makedirs(os.path.dirname(full), exist_ok=True)
        open(full, "w").write("X = 1\n")
        _commit(repo, "nested module")
        json.dump(manifest_record(paths, "synthetic test"), open(paths.manifest, "w"))
        assert NESTED in json.load(open(paths.manifest))["code_identity"]["files"]
    if change == "added":
        os.makedirs(os.path.dirname(full), exist_ok=True)
        open(full, "w").write("X = 1\n")
    elif change == "modified":
        open(full, "a").write("X = 2\n")
    else:
        os.remove(full)
    _commit(repo)
    with pytest.raises(RunControlError, match=f"{change} \\['{NESTED}'\\]"):
        open_run(paths, "synthetic test", now=clock())


def test_record_appearing_in_place_of_an_acknowledged_missing_record_is_detected(paths, clock):
    """A record acknowledged as missing cannot be replaced by a different record with the same sequence number."""
    _run(paths, clock)
    _write_lines(paths, _lines(paths)[:-1])
    r1 = _recover(paths, clock)
    p1 = os.path.join(paths.recoveries, f"{r1['recovery_id']}.json")
    substitute = json.load(open(p1))
    os.remove(p1)
    _recover(paths, clock, "record 1 lost")            # record 2 acknowledges record 1 as missing
    substitute["recovery_id"] = "20261202T000000Z-r001-substit"
    json.dump(substitute, open(os.path.join(paths.recoveries, substitute["recovery_id"] + ".json"), "w"))
    with pytest.raises(RunControlError, match="is not acknowledged by the latest recovery record"):
        reconcile(paths)


def test_latest_record_must_list_every_earlier_recovery(paths, clock):
    """Even if the latest record and its log entry are rewritten consistently, a record that omits an earlier
    sequence number is detected (the sequence numbers themselves are evidence of earlier recoveries)."""
    _run(paths, clock)
    os.remove(paths.log)
    r1 = _recover(paths, clock)
    os.remove(paths.log)
    r2 = _recover(paths, clock)
    os.remove(os.path.join(paths.recoveries, f"{r1['recovery_id']}.json"))
    p2 = os.path.join(paths.recoveries, f"{r2['recovery_id']}.json")
    rec = json.load(open(p2))
    rec["prior_recoveries"], rec["prev_record_sha256"] = [], None      # record 1 erased from the chain
    _writable(p2)
    json.dump(rec, open(p2, "w"), indent=2, sort_keys=True)
    lines = _lines(paths)
    last = json.loads(lines[-1])
    last["record_sha256"] = _sha(p2)                                    # log entry forged to match
    lines[-1] = (json.dumps(last, sort_keys=True) + "\n").encode()
    _write_lines(paths, lines)
    with pytest.raises(RunControlError, match="does not list every earlier recovery"):
        reconcile(paths)


def test_unexpected_exception_inside_close_verification_is_an_integrity_failure(paths, clock, monkeypatch):
    """Any exception type raised inside the verification boundary (not only RunControlError) closes the run as
    aborted, with the original exception chained."""
    run = open_run(paths, "synthetic test", now=clock())

    def broken(*a, **k):
        raise KeyError("unexpected failure inside verification")
    monkeypatch.setattr(run_control, "verify_code", broken)
    with pytest.raises(RunControlError, match="closed as aborted: KeyError") as ei:
        close_run(run)
    assert isinstance(ei.value.__cause__, KeyError)
    close = json.load(open(os.path.join(run.run_dir, "close.json")))
    assert close["status"] == "aborted" and "KeyError" in close["error"]
    assert json.loads(_lines(paths)[-1])["event"] == "aborted"


@pytest.mark.parametrize("target", ["prefix_line", "recovery_entry_link"])
def test_preserved_prefix_and_recovery_entry_cannot_be_edited_after_recovery(paths, clock, target):
    _run(paths, clock)
    _write_lines(paths, _lines(paths)[:-1])
    _recover(paths, clock)
    lines = _lines(paths)
    if target == "prefix_line":                         # an acknowledged, preserved line edited afterwards
        lines[0] = lines[0].replace(b"synthetic test", b"someone else")
    else:                                               # the recovery entry's own link to the prefix edited
        e = json.loads(lines[-1])
        e["prev_sha256"] = "f" * 64
        lines[-1] = (json.dumps(e, sort_keys=True) + "\n").encode()
    _write_lines(paths, lines)
    with pytest.raises(RunControlError, match="does not match the preserved log prefix"):
        reconcile(paths)


def test_editing_an_earlier_preserved_line_is_detected_by_the_prefix_hash(paths, clock):
    """An edit to a preserved line that is NOT adjacent to the recovery entry changes no link; only the
    recorded prefix hash can reveal it."""
    _run(paths, clock)
    _run(paths, clock)
    _write_lines(paths, _lines(paths)[:-1])           # 3 preserved lines remain
    _recover(paths, clock)
    lines = _lines(paths)
    lines[0] = lines[0].replace(b"synthetic test", b"someone else")
    _write_lines(paths, lines)
    with pytest.raises(RunControlError, match="does not match the preserved log prefix"):
        reconcile(paths)
