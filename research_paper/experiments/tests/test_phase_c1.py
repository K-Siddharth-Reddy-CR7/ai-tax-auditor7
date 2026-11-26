"""Phase C.1 (IMPLEMENTATION_PLAN.md): run-log reconciliation and recovery (R1), code identity pinned at freeze
(R2), provenance re-checks (R3), the full-pipeline DEV risk-coverage grid, and the documented tie-breaks.

Everything uses synthetic benchmarks, synthetic manifests, temporary git repositories and temporary run
directories. Nothing is written to the real results/ directory, and no real manifest is created.
"""
import datetime
import hashlib
import json
import os
import shutil
import stat

import pytest
from _runfix import git, make_code_repo, make_paths
from test_eval_exclusions import SYN_PRODUCT, syn  # noqa: F401  (fixture)

import run_all
from lexeval import evaluate, figures, run_control, tuning
from lexeval.paths import GEN, RESULTS, config
from lexeval.run_control import (GENESIS, RunControlError, close_run, code_identity, manifest_record, open_run,
                                 reconcile, recover)
from lexeval.systems import primary_systems
from lexeval.tuning import TuningRecordError

T0 = datetime.datetime(2026, 12, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)


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


def _two_runs(paths):
    a = open_run(paths, "synthetic test", now=_at(0))
    close_run(a)
    b = open_run(paths, "synthetic test", rerun_reason="second", now=_at(1))
    close_run(b)
    return a, b


def _lines(paths):
    return open(paths.log, "rb").read().splitlines(keepends=True)


def _write(paths, lines):
    open(paths.log, "wb").write(b"".join(lines))


def _refused(paths, match):
    with pytest.raises(RunControlError, match=match):
        reconcile(paths)
    with pytest.raises(RunControlError):
        open_run(paths, "synthetic test", rerun_reason="after tampering", now=_at(30))


# ========================================================================== R1: reconciliation
def test_valid_first_run_with_no_evidence(paths):
    assert reconcile(paths) == {"previous": [], "status": {}, "interrupted": []}
    run = open_run(paths, "synthetic test", now=_at(0))
    close_run(run)
    assert reconcile(paths)["status"] == {run.run_id: "completed"}


def test_valid_subsequent_run_records_previous(paths):
    a, b = _two_runs(paths)
    st = reconcile(paths)
    assert st["previous"] == [a.run_id, b.run_id] and b.start_record["previous_runs"] == [a.run_id]


def test_entire_log_deleted(paths):
    _two_runs(paths)
    os.remove(paths.log)
    _refused(paths, "log is missing but evidence")


def test_whole_line_tail_truncation(paths):
    _two_runs(paths)
    lines = _lines(paths)
    _write(paths, lines[:-1])                      # last 'completed' entry removed
    _refused(paths, "closed on disk but the log has no end entry")
    _write(paths, lines[:-2])                      # last run's 'started' and 'completed' removed
    _refused(paths, "orphaned run directory")


def test_middle_entry_deleted(paths):
    _two_runs(paths)
    lines = _lines(paths)
    _write(paths, lines[:1] + lines[2:])
    _refused(paths, "hash chain broken")


def test_reordered_entries(paths):
    _two_runs(paths)
    lines = _lines(paths)
    _write(paths, [lines[1], lines[0]] + lines[2:])
    _refused(paths, "hash chain broken")


@pytest.mark.parametrize("where", ["end", "middle"])
def test_duplicate_entries(paths, where):
    _two_runs(paths)
    lines = _lines(paths)
    _write(paths, lines + [lines[0]] if where == "end" else lines[:2] + [lines[1]] + lines[2:])
    _refused(paths, "hash chain broken")


def test_truncated_last_line(paths):
    _two_runs(paths)
    lines = _lines(paths)
    _write(paths, lines[:-1] + [lines[-1][:-10]])
    _refused(paths, "run log")


def test_orphaned_run_directory(paths):
    _two_runs(paths)
    os.mkdir(os.path.join(paths.runs, "20261201T120000Z-deadbeef"))
    _refused(paths, "orphaned run directory 20261201T120000Z-deadbeef")


def test_missing_run_directory(paths):
    a, _ = _two_runs(paths)
    shutil.rmtree(a.run_dir)                       # temporary copy only
    _refused(paths, f"{a.run_id} is in the log but its directory is missing")


@pytest.mark.parametrize("damage", ["missing", "corrupt", "modified"])
def test_missing_or_corrupted_run_json(paths, damage):
    a, _ = _two_runs(paths)
    p = os.path.join(a.run_dir, "run.json")
    os.chmod(p, stat.S_IWUSR | stat.S_IRUSR)
    if damage == "missing":
        os.remove(p)
        match = "run.json missing or corrupt"
    elif damage == "corrupt":
        open(p, "w").write("{not json")
        match = "run.json missing or corrupt"
    else:
        rec = json.load(open(p))
        rec["authorised_by"] = "someone else"
        json.dump(rec, open(p, "w"))
        match = "run.json differs"
    _refused(paths, match)


def test_modified_or_added_outputs_detected(paths):
    a, _ = _two_runs(paths)
    p = os.path.join(a.run_dir, "outputs_sha256.json")
    os.chmod(p, stat.S_IWUSR | stat.S_IRUSR)
    with open(os.path.join(a.run_dir, "late_addition.txt"), "w") as fh:
        fh.write("x")
    _refused(paths, "files added after closing")


def _rechain(entries):
    """Simulates a DELIBERATE, consistent rewrite of the whole log (used to test the limits)."""
    out, prev = [], GENESIS
    for e in entries:
        e = dict(e, prev_sha256=prev)
        line = json.dumps(e, sort_keys=True).encode()
        out.append(line + b"\n")
        prev = hashlib.sha256(line).hexdigest()
    return out


def test_previous_run_references_checked_even_in_a_rechained_log(paths):
    a, b = _two_runs(paths)
    entries = [json.loads(x) for x in _lines(paths)]
    entries[2]["previous_runs"] = []               # b claims no earlier run
    _write(paths, _rechain(entries))
    _refused(paths, "previous runs")


def test_malformed_run_id_detected(paths):
    run = open_run(paths, "synthetic test", now=_at(0))
    close_run(run)
    entries = [json.loads(x) for x in _lines(paths)]
    bad = "not-a-run-id"
    for e in entries:
        e["run_id"] = bad
    os.rename(run.run_dir, os.path.join(paths.runs, bad))
    d = os.path.join(paths.runs, bad)
    for f in ("run.json", "close.json"):
        os.chmod(os.path.join(d, f), stat.S_IWUSR | stat.S_IRUSR)
        rec = json.load(open(os.path.join(d, f)))
        rec["run_id"] = bad
        json.dump(rec, open(os.path.join(d, f), "w"))
    _write(paths, _rechain(entries))
    _refused(paths, "malformed run id")


def test_documented_limit_consistent_rewrite_of_all_evidence(paths):
    """LIMIT (documented, not a safeguard): deleting a run directory AND consistently rewriting the log so that
    the run never appears is not detectable locally. The chain has no secret key."""
    a, b = _two_runs(paths)
    entries = [json.loads(x) for x in _lines(paths)][:2]
    shutil.rmtree(b.run_dir)
    _write(paths, _rechain(entries))
    assert reconcile(paths)["previous"] == [a.run_id]


def test_interrupted_run_is_a_documented_state_and_counts_as_previous(paths):
    """Phase C.2 (D4) makes this stricter: an interrupted run reconciles, but no new TEST run is allowed until a
    recovery has acknowledged it (the protection point of its outputs). It still counts as an earlier run."""
    run = open_run(paths, "synthetic test", now=_at(0))   # never closed (e.g. the process was killed)
    run_control._OPEN_RUNS.pop(run.run_id)
    assert reconcile(paths)["status"] == {run.run_id: "started"}
    assert reconcile(paths)["interrupted"] == [run.run_id]
    with pytest.raises(RunControlError, match="must be acknowledged"):
        open_run(paths, "synthetic test", rerun_reason="after interrupted run", now=_at(1))
    recover(paths, "author one", "acknowledge interrupted run")
    with pytest.raises(RunControlError, match="rerun-reason"):
        open_run(paths, "synthetic test", now=_at(1))
    nxt = open_run(paths, "synthetic test", rerun_reason="after interrupted run", now=_at(1))
    assert nxt.start_record["previous_runs"] == [run.run_id]
    close_run(nxt)


# ------------------------------------------------------------------------ R1: recovery procedure
def test_recovery_requires_authorisation_reason_and_a_problem(paths):
    _two_runs(paths)
    with pytest.raises(RunControlError, match="nothing to recover"):
        recover(paths, "author", "reason")
    os.remove(paths.log)
    for who, why in (("", "reason"), ("author", ""), (None, None)):
        with pytest.raises(RunControlError, match="authorised-by and --recovery-reason"):
            recover(paths, who, why)
    with pytest.raises(SystemExit, match="Recovery refused"):
        run_all.stage_recover_runs("", "", paths=paths)


def test_recovery_after_log_deletion_preserves_evidence(paths):
    a, b = _two_runs(paths)
    dirs_before = {r: _tree(os.path.join(paths.runs, r)) for r in os.listdir(paths.runs)}
    os.remove(paths.log)
    rec = run_all.stage_recover_runs("author one", "log deleted by mistake", paths=paths)
    assert rec["log_missing"] and set(rec["acknowledged_runs"]) == {a.run_id, b.run_id}
    assert any("log is missing" in p for p in rec["problems"])
    assert {r: _tree(os.path.join(paths.runs, r)) for r in os.listdir(paths.runs)} == dirs_before
    st = reconcile(paths)
    assert st["previous"] == sorted([a.run_id, b.run_id])
    with pytest.raises(RunControlError, match="rerun-reason"):          # acknowledged runs count as earlier runs
        open_run(paths, "synthetic test", now=_at(5))
    c = open_run(paths, "synthetic test", rerun_reason="after recovery", now=_at(5))
    assert c.start_record["previous_runs"] == sorted([a.run_id, b.run_id])
    close_run(c)
    reconcile(paths)


def test_recovery_after_truncation_keeps_the_original_log_bytes(paths):
    _two_runs(paths)
    lines = _lines(paths)
    _write(paths, lines[:-1])
    before = open(paths.log, "rb").read()
    rec = recover(paths, "author one", "completed entry lost")
    after = open(paths.log, "rb").read()
    assert after.startswith(before) and after.count(b"\n") == before.count(b"\n") + 1
    assert rec["log_sha256_at_recovery"] == hashlib.sha256(before).hexdigest()
    reconcile(paths)


def test_recovered_state_is_still_protected(paths):
    a, b = _two_runs(paths)
    os.remove(paths.log)
    rec = recover(paths, "author one", "log deleted")
    p = os.path.join(a.run_dir, "run.json")
    os.chmod(p, stat.S_IWUSR | stat.S_IRUSR)
    with open(p, "a") as fh:
        fh.write(" ")
    _refused(paths, f"acknowledged run {a.run_id} is missing or changed")
    with open(p, "rb+") as fh:                      # undo, then remove the recovery record instead
        data = fh.read()
        fh.seek(0)
        fh.write(data[:-1])
        fh.truncate()
    reconcile(paths)
    rec_file = os.path.join(paths.recoveries, rec["recovery_id"] + ".json")
    os.chmod(rec_file, stat.S_IWUSR | stat.S_IRUSR)
    with open(rec_file, "a") as fh:
        fh.write(" ")
    _refused(paths, "recovery record")


def test_recovery_record_without_log_entry_is_detected(paths):
    _two_runs(paths)
    os.remove(paths.log)
    recover(paths, "author one", "log deleted")
    lines = _lines(paths)
    _write(paths, [])                               # recovery entry lost as well
    os.remove(paths.log)
    _refused(paths, "log is missing but evidence")


# ========================================================================== R2: code identity
def test_manifest_records_code_identity_and_commit(paths):
    man = json.load(open(paths.manifest))
    ci = man["code_identity"]
    assert ci["git_commit"] == git(paths.code_root, "rev-parse", "HEAD")
    assert ci["sha256"] == code_identity(paths.code_root)["sha256"]
    assert ci["patterns"] == run_control.CODE_IDENTITY_PATTERNS
    assert "research_paper/experiments/lexeval/evaluate.py" in ci["files"] and "backend/server.py" in ci["files"]
    assert not [f for f in ci["files"] if "/tests/" in f or f.endswith(".md") or "results/" in f]


def test_code_identity_is_deterministic_and_ignores_non_code(tmp_path):
    a, b = make_code_repo(tmp_path / "a"), make_code_repo(tmp_path / "b")
    assert code_identity(a)["sha256"] == code_identity(b)["sha256"]
    os.makedirs(os.path.join(a, "research_paper/experiments/tests"), exist_ok=True)
    open(os.path.join(a, "research_paper/experiments/tests/test_new.py"), "w").write("x")
    open(os.path.join(a, "NOTES.md"), "w").write("x")
    assert code_identity(a)["sha256"] == code_identity(b)["sha256"]


def test_freeze_refuses_dirty_tree_and_never_overwrites(syn, tmp_path, monkeypatch):
    p = make_paths(tmp_path, syn["gen"], syn["path"], syn["pilot"], write_manifest=False)
    monkeypatch.setattr(run_all, "freeze_preconditions", lambda: [])   # preconditions are tested in Phase A
    open(os.path.join(p.code_root, "scratch.txt"), "w").write("uncommitted")
    with pytest.raises(RunControlError, match="not clean"):
        manifest_record(p, "author")
    with pytest.raises(SystemExit, match="not clean"):
        run_all.stage_freeze("author", paths=p)
    assert not os.path.exists(p.manifest)
    os.remove(os.path.join(p.code_root, "scratch.txt"))
    run_all.stage_freeze("author", paths=p)
    man = json.load(open(p.manifest))
    assert man["code_identity"]["git_commit"] and man["approved_by"] == "author"
    before = open(p.manifest, "rb").read()
    with pytest.raises(SystemExit, match="never overwritten"):
        run_all.stage_freeze("author", paths=p)
    assert open(p.manifest, "rb").read() == before


def _edit(repo, rel, text, commit=True):
    full = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "a") as fh:
        fh.write(text)
    if commit:
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "change")


@pytest.mark.parametrize("change,match", [
    ("modified_uncommitted", "not clean|code changed"),
    ("modified_committed", "modified \\['research_paper/experiments/lexeval/evaluate.py'\\]"),
    ("added_committed", "added \\['research_paper/experiments/lexeval/new_module.py'\\]"),
    ("deleted_committed", "deleted \\['backend/lexitax_v2/product.py'\\]"),
    ("table_data_committed", "modified \\['taxes.json'\\]"),
    ("not_descendant", "does not descend from the frozen commit"),
    ("dirty_non_code", "not clean"),
])
def test_test_run_refused_when_code_or_tree_changed(paths, change, match):
    repo = paths.code_root
    if change == "modified_uncommitted":
        _edit(repo, "research_paper/experiments/lexeval/evaluate.py", "\n# changed\n", commit=False)
    elif change == "modified_committed":
        _edit(repo, "research_paper/experiments/lexeval/evaluate.py", "\n# changed\n")
    elif change == "added_committed":
        _edit(repo, "research_paper/experiments/lexeval/new_module.py", "x = 1\n")
    elif change == "deleted_committed":
        os.remove(os.path.join(repo, "backend/lexitax_v2/product.py"))
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "delete")
    elif change == "table_data_committed":
        _edit(repo, "taxes.json", " ")
    elif change == "not_descendant":
        git(repo, "checkout", "-q", "--orphan", "rewritten")
        git(repo, "commit", "-q", "-m", "same files, rewritten history")
    elif change == "dirty_non_code":
        _edit(repo, "notes/untracked.txt", "x", commit=False)
    with pytest.raises(RunControlError, match=match):
        open_run(paths, "synthetic test", now=_at(0))
    assert not os.path.exists(paths.runs)


def test_descendant_commit_without_code_changes_is_allowed(paths):
    """E.g. committing MANIFEST.json, the DEV tuning outputs or documentation after the freeze."""
    _edit(paths.code_root, "research_paper/experiments/results/tuning_dev.json", "{}")
    _edit(paths.code_root, "docs/notes.md", "x")
    run = open_run(paths, "synthetic test", now=_at(0))
    assert run.start_record["frozen_git_commit"] != run.start_record["git_head"]
    close_run(run)


def test_code_change_during_run_closes_it_as_aborted(paths):
    run = open_run(paths, "synthetic test", now=_at(0))
    _edit(paths.code_root, "backend/server.py", "\n# changed during run\n")
    with pytest.raises(RunControlError, match="closed as aborted"):
        close_run(run)
    last = json.loads(_lines(paths)[-1])
    assert last["event"] == "aborted" and "code changed" in last["error"]
    assert json.load(open(os.path.join(run.run_dir, "close.json")))["status"] == "aborted"
    reconcile(paths)                                # the aborted run is preserved and consistent


# ========================================================================== R3: provenance re-checks
def test_tuning_record_changed_after_open_is_refused(paths):
    run = open_run(paths, "synthetic test", now=_at(0))
    expected = run.start_record["hashes"]["tuning_record_sha256"]
    assert tuning.load_tuned(paths.tuning, expected_sha256=expected)
    rec = json.load(open(paths.tuning))
    rec["chosen"]["product_min_coverage"] = 1.0
    json.dump(rec, open(paths.tuning, "w"))
    with pytest.raises(TuningRecordError):
        tuning.load_tuned(paths.tuning, expected_sha256=expected)
    close_run(run, "aborted", error="test")


def test_stage_evaluate_refuses_tuning_change_between_open_and_load(paths, monkeypatch):
    real_open = run_control.open_run

    def open_then_tamper(*a, **k):
        run = real_open(*a, **k)
        rec = json.load(open(paths.tuning))
        rec["chosen"]["product_typo_max_edits"] = 2
        json.dump(rec, open(paths.tuning, "w"))
        return run
    monkeypatch.setattr(run_control, "open_run", open_then_tamper)
    with pytest.raises(TuningRecordError):
        run_all.stage_evaluate({}, "test", "synthetic test", paths=paths)
    events = [json.loads(x)["event"] for x in _lines(paths)]
    assert events == ["started", "aborted"]


@pytest.mark.parametrize("what", ["benchmark", "exclusions", "config_record"])
def test_manifest_rechecked_at_close(paths, what):
    run = open_run(paths, "synthetic test", now=_at(0))
    evaluate.evaluate(primary_systems(), "test", "primary", run=run)
    if what == "benchmark":
        open(os.path.join(paths.gen, "country_benchmark.csv"), "a").write("\n")
    elif what == "exclusions":
        open(paths.exclusions, "a").write("\n")
    else:
        man = json.load(open(paths.manifest))
        man["config_sha256"] = "0" * 64
        json.dump(man, open(paths.manifest, "w"))
    with pytest.raises(RunControlError, match="closed as aborted"):
        close_run(run)
    assert json.load(open(os.path.join(run.run_dir, "close.json")))["status"] == "aborted"
    assert os.path.exists(os.path.join(run.run_dir, "processed", "primary_test_product_summary.csv"))


def test_run_json_records_environment(paths):
    run = open_run(paths, "synthetic test", now=_at(0))
    env = run.start_record["environment"]
    assert env["python"] and "numpy" in env["packages"] and "pycountry" in env["packages"]
    assert run.start_record["frozen_git_commit"] == json.load(open(paths.manifest))["code_identity"]["git_commit"]
    with pytest.raises(ValueError):
        close_run(run, "finished")
    close_run(run)


# ========================================================================== risk-coverage: full-pipeline grid
CFG = {"tuning_rule": "test rule", "tuning_grid": {"product_min_coverage": [0.0, 0.5, 1.0],
                                                   "product_typo_max_edits": [0, 1], "product_typo_min_len": [4, 5]}}


@pytest.fixture
def dev_bundle(syn, tmp_path):
    tj = tmp_path / "tuning_dev.json"
    s1c, rec = tuning.tune(CFG, gen_dir=syn["gen"], out_path=str(tj))
    dev = tmp_path / "dev"
    evaluate.evaluate(primary_systems(s1c), "dev", "primary", gen_dir=syn["gen"], out_dir=str(dev))
    gj = dev / "grid_full_pipeline_dev.json"
    grid = tuning.full_pipeline_grid(CFG, rec, gen_dir=syn["gen"], out_path=str(gj))
    return {"tj": tj, "rec": rec, "dev": dev, "gj": gj, "grid": grid, "syn": syn}


def test_full_pipeline_grid_covers_every_setting_with_both_levels(dev_bundle):
    grid, rec = dev_bundle["grid"], dev_bundle["rec"]
    settings = list(tuning.grid_settings(CFG["tuning_grid"]))
    assert grid["n_settings"] == len(settings) == len(rec["grid"]) == 9
    for g in grid["grid"]:
        assert set(g) >= {"resolver_level", "full_pipeline", "difference_full_minus_resolver"}
        r, f = g["resolver_level"]["dev_pooled_P1_P7"], g["full_pipeline"]["dev_pooled_P1_P7"]
        assert g["difference_full_minus_resolver"]["coverage"] == pytest.approx(f["coverage"] - r["coverage"])
    assert grid["selected_setting"] == rec["chosen"] and grid["split"] == "dev"
    assert grid["selection_basis"].startswith("resolver-level")
    assert json.load(open(dev_bundle["gj"]))["n_settings"] == 9
    with pytest.raises(FileExistsError):
        tuning.full_pipeline_grid(CFG, rec, gen_dir=dev_bundle["syn"]["gen"], out_path=str(dev_bundle["gj"]))


def test_selected_s1_point_matches_its_full_pipeline_grid_point(dev_bundle):
    made = figures.dev_figures(str(dev_bundle["dev"]), str(dev_bundle["tj"]), str(dev_bundle["gj"]))
    cmp_ = made["dev_risk_coverage.pdf"]["s1_operating_point_vs_grid"]
    assert cmp_["s1_system_point"] == cmp_["selected_grid_point"]
    assert all(v in (0, 0.0, None) for v in cmp_["difference_system_minus_grid"].values())
    assert made["dev_risk_coverage.pdf"]["title"] == "S1 full-pipeline risk\u2013coverage across the tuning grid (DEV)"
    assert made["dev_risk_coverage.pdf"]["selection_basis"].startswith("resolver-level")


def test_grid_differences_are_preserved_not_forced(syn, tmp_path, monkeypatch):
    """If the full pipeline behaves differently from the resolver, the difference is recorded as computed, the
    figure is still drawn, and selection (the tuning record) is unaffected."""
    tj = tmp_path / "t.json"
    s1c, rec = tuning.tune(CFG, gen_dir=syn["gen"], out_path=str(tj))
    record_before = open(tj, "rb").read()
    from lexeval import systems
    real = systems.run_S1

    def perturbed(product, *a, **k):
        out = real(product, *a, **k)
        return dict(out, prod_hs=None) if product == "Memory Card" else out
    monkeypatch.setattr(systems, "run_S1", perturbed)
    grid = tuning.full_pipeline_grid(CFG, rec, gen_dir=syn["gen"])
    assert grid["n_settings_with_differences"] > 0
    assert any(g["difference_full_minus_resolver"]["coverage"] < 0 for g in grid["grid"])
    assert open(tj, "rb").read() == record_before and grid["selected_setting"] == rec["chosen"]


def test_grid_refuses_non_dev_or_mismatched_records(dev_bundle):
    rec = dict(dev_bundle["rec"], split="test")
    with pytest.raises(TuningRecordError):
        tuning.full_pipeline_grid(CFG, rec, gen_dir=dev_bundle["syn"]["gen"])
    other = {"tuning_rule": "x", "tuning_grid": {"product_min_coverage": [0.25], "product_typo_max_edits": [0],
                                                 "product_typo_min_len": [4]}}
    with pytest.raises(TuningRecordError, match="grid differs"):
        tuning.full_pipeline_grid(other, dev_bundle["rec"], gen_dir=dev_bundle["syn"]["gen"])


def test_grid_uses_only_dev_inputs(dev_bundle, monkeypatch):
    seen = []
    from lexeval import systems
    real = systems.run_S1
    monkeypatch.setattr(systems, "run_S1", lambda p, *a, **k: seen.append(p) or real(p, *a, **k))
    tuning.full_pipeline_grid(CFG, dev_bundle["rec"], gen_dir=dev_bundle["syn"]["gen"])
    assert set(seen) == {r["text"] for r in SYN_PRODUCT if r["split"] == "dev"}


def test_production_grid_size():
    """The configured grid has 49 settings (7 x (1 + 2 x 3)); min_len is irrelevant without typo edits."""
    assert len(list(tuning.grid_settings(config()["tuning_grid"]))) == 49


# ========================================================================== documented tie-breaks
def _g(cov, k, m, acc, ser):
    return dict(product_min_coverage=cov, product_typo_max_edits=k, product_typo_min_len=m,
                dev_macro_decision_accuracy=acc, dev_macro_silent_error_rate=ser)


@pytest.mark.parametrize("grid,expected", [
    ([_g(0.5, 1, 5, 0.99, 0.20), _g(0.5, 1, 5, 0.10, 0.15)], (0.5, 1, 5, 0.10)),     # 1. lowest SER wins
    ([_g(0.75, 1, 5, 0.60, 0.15), _g(0.5, 1, 5, 0.70, 0.15)], (0.5, 1, 5, 0.70)),    # 2. SER tie -> higher accuracy
    #    (accuracy outranks the coverage-threshold tie-break: the higher-accuracy setting has the SMALLER threshold)
    ([_g(0.5, 1, 5, 0.70, 0.15), _g(0.75, 1, 5, 0.70, 0.15)], (0.75, 1, 5, 0.70)),   # 3. -> larger coverage threshold
    ([_g(0.5, 2, 5, 0.70, 0.15), _g(0.5, 1, 5, 0.70, 0.15)], (0.5, 1, 5, 0.70)),     # 4. -> fewer typo edits
    ([_g(0.5, 1, 4, 0.70, 0.15), _g(0.5, 1, 6, 0.70, 0.15)], (0.5, 1, 6, 0.70)),     # 5. -> longer minimum length
])
def test_infeasible_tie_breaks_match_documentation(grid, expected):
    chosen, rule = tuning.select(grid, b_ser=0.01)
    assert rule.startswith("infeasible")
    got = (chosen["product_min_coverage"], chosen["product_typo_max_edits"], chosen["product_typo_min_len"],
           chosen["dev_macro_decision_accuracy"])
    assert got == expected
    assert tuning.INFEASIBLE_ORDER == ("lowest DEV macro silent-error rate", "higher DEV macro decision accuracy",
                                       "larger product_min_coverage", "fewer product_typo_max_edits",
                                       "longer product_typo_min_len")


@pytest.mark.parametrize("grid,expected", [
    ([_g(0.5, 1, 5, 0.80, 0.05), _g(0.75, 1, 5, 0.70, 0.01)], (0.5, 1, 5)),          # highest accuracy among feasible
    ([_g(0.5, 1, 5, 0.80, 0.05), _g(0.75, 1, 5, 0.80, 0.09)], (0.75, 1, 5)),         # -> larger coverage threshold
    ([_g(0.5, 2, 5, 0.80, 0.05), _g(0.5, 1, 5, 0.80, 0.05)], (0.5, 1, 5)),           # -> fewer typo edits
    ([_g(0.5, 1, 4, 0.80, 0.05), _g(0.5, 1, 6, 0.80, 0.05)], (0.5, 1, 6)),           # -> longer minimum length
    ([_g(0.5, 1, 5, 0.99, 0.20), _g(0.75, 1, 5, 0.70, 0.10)], (0.75, 1, 5)),         # infeasible ones never chosen
])
def test_feasible_tie_breaks_match_documentation(grid, expected):
    chosen, rule = tuning.select(grid, b_ser=0.10)
    assert rule.startswith("max dev accuracy")
    assert (chosen["product_min_coverage"], chosen["product_typo_max_edits"], chosen["product_typo_min_len"]) == expected


def test_tie_break_documentation_is_recorded(tmp_path, syn):
    _, rec = tuning.tune(CFG, gen_dir=syn["gen"], out_path=str(tmp_path / "t.json"))
    assert rec["tie_breaks"] == {"feasible": list(tuning.FEASIBLE_ORDER), "infeasible": list(tuning.INFEASIBLE_ORDER)}
    assert "if tied, higher DEV macro decision accuracy" in tuning.__doc__
