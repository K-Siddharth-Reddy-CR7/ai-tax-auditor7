"""Phase C (IMPLEMENTATION_PLAN.md): TEST route, per-item guards, DEV-only tuning and latency, figure paths,
ladder evaluation and permanent TEST run controls.

Everything runs on SYNTHETIC benchmarks and manifests in pytest temporary directories (see _runfix.py and the
Phase B synthetic benchmark). No real TEST item is scored, no real tuning or latency run is made, and nothing is
written to the real results/ directory or MANIFEST.json.
"""
import csv
import hashlib
import json
import os
import stat

import pytest
from _runfix import make_paths
from test_eval_exclusions import AUTHORISED, SENTINELS, SYN_COUNTRY, SYN_PRODUCT, syn  # noqa: F401  (fixture)

import run_all
from lexeval import eval_exclusions, evaluate, figures, latency, run_control, tuning
from lexeval.build_common import read_csv
from lexeval.eval_exclusions import EvaluationExclusionError
from lexeval.figures import FigureInputError
from lexeval.latency import LatencySplitError
from lexeval.paths import EXP, GEN, RESULTS
from lexeval.run_control import AuthorisedTestRun, RunControlError, close_run, open_run, read_log
from lexeval.systems import ladder_systems, primary_systems
from lexeval.tuning import TuningSplitError

TEST_SCORED_P = {r["item_id"] for r in SYN_PRODUCT if r["split"] == "test"} - set(AUTHORISED)
TEST_SCORED_C = {r["item_id"] for r in SYN_COUNTRY if r["split"] == "test"} - set(AUTHORISED)
DEV_P = [r for r in SYN_PRODUCT if r["split"] == "dev"]
DEV_C = [r for r in SYN_COUNTRY if r["split"] == "dev"]


@pytest.fixture(autouse=True)
def _real_results_untouched():
    """No Phase C test may create or change anything in the real results/ directory or create MANIFEST.json."""
    before = sorted(os.listdir(RESULTS)) if os.path.exists(RESULTS) else None
    yield
    after = sorted(os.listdir(RESULTS)) if os.path.exists(RESULTS) else None
    assert before == after, "a test wrote to the real results/ directory"
    assert not os.path.exists(os.path.join(GEN, "MANIFEST.json"))


@pytest.fixture
def paths(syn, tmp_path):
    return make_paths(tmp_path, syn["gen"], syn["path"], syn["pilot"])


def _recorder(calls):
    sysd = primary_systems()

    def wrap(name, fn):
        def inner(*a):
            calls.append((name, a))
            return fn(*a)
        return inner
    return {k: wrap(k, v) for k, v in sysd.items()}


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _files(d):
    out = {}
    for root, _, files in os.walk(d):
        for f in files:
            out[os.path.relpath(os.path.join(root, f), d)] = _sha(os.path.join(root, f))
    return out


# ============================================================== A. per-item scoring functions
@pytest.mark.parametrize("task,rows", [("product", SYN_PRODUCT), ("country", SYN_COUNTRY)])
def test_scoring_functions_reject_excluded_ids_before_running_anything(task, rows, paths):
    fn = evaluate.run_product_task if task == "product" else evaluate.run_country_task
    excluded = [r for r in rows if r["item_id"] in AUTHORISED]
    calls = []
    run = open_run(paths, "synthetic test")  # even inside an authorised run
    for items in (excluded, [dict(r, split="dev") for r in excluded]):  # relabelling as DEV does not help
        with pytest.raises(EvaluationExclusionError):
            fn(items, _recorder(calls), run=run)
    assert calls == []
    close_run(run)


@pytest.mark.parametrize("task,rows", [("product", SYN_PRODUCT), ("country", SYN_COUNTRY)])
def test_scoring_functions_refuse_test_rows_outside_an_authorised_run(task, rows, tmp_path):
    fn = evaluate.run_product_task if task == "product" else evaluate.run_country_task
    test_rows = [r for r in rows if r["split"] == "test" and r["item_id"] not in AUTHORISED]
    forged = AuthorisedTestRun("forged", str(tmp_path), None, {"evaluation_exclusions_sha256": "x"}, {})
    calls = []
    for run in (None, forged):
        with pytest.raises(RunControlError):
            fn(test_rows, _recorder(calls), run=run)
    assert calls == []


@pytest.mark.parametrize("bad", [None, "", "train", "TEST"])
def test_scoring_functions_require_a_known_split(bad):
    row = dict(DEV_P[1])
    if bad is None:
        row.pop("split")
    else:
        row["split"] = bad
    with pytest.raises(ValueError, match="split"):
        evaluate.run_product_task([row], primary_systems())


def test_scoring_functions_accept_dev_rows_normally():
    p = evaluate.run_product_task(DEV_P, primary_systems())
    c = evaluate.run_country_task(DEV_C, primary_systems())
    assert len(p) == len(DEV_P) * 3 and len(c) == len(DEV_C) * 3
    assert {r["split"] for r in p + c} == {"dev"} and all(r["propagation"] for r in p + c)


def test_scoring_functions_accept_test_rows_inside_an_open_run(paths):
    run = open_run(paths, "synthetic test")
    rows = [r for r in SYN_PRODUCT if r["item_id"] in TEST_SCORED_P]
    out = evaluate.run_product_task(rows, primary_systems(), run=run, exclusions_path=paths.exclusions)
    assert {r["item_id"] for r in out} == TEST_SCORED_P and {r["split"] for r in out} == {"test"}
    close_run(run)
    with pytest.raises(RunControlError):  # closed runs no longer authorise anything
        evaluate.run_product_task(rows, primary_systems(), run=run)


# ============================================================== B. run_all is the only TEST route
def test_evaluate_and_load_refuse_test_without_open_run(paths):
    with pytest.raises(RunControlError):
        evaluate.load("test")
    run = open_run(paths, "synthetic test")
    close_run(run)
    with pytest.raises(RunControlError):
        evaluate.evaluate(primary_systems(), "test", "primary", run=run)


def test_evaluate_has_no_caller_supplied_hash_parameter():
    import inspect
    params = set(inspect.signature(evaluate.evaluate).parameters) | set(inspect.signature(evaluate.load).parameters)
    assert not {p for p in params if "sha" in p or "exclusions_path" in p or "pilot" in p}


def test_dev_evaluation_rejects_a_test_run_handle(paths, tmp_path):
    run = open_run(paths, "synthetic test")
    with pytest.raises(RunControlError):
        evaluate.evaluate(primary_systems(), "dev", "x", run=run, gen_dir=paths.gen, out_dir=str(tmp_path / "d"))
    close_run(run)


@pytest.mark.parametrize("change", ["benchmark", "exclusions", "config_hash", "treatments_hash", "audit",
                                    "approved_by", "no_manifest"])
def test_open_run_verifies_every_manifest_hash(paths, change):
    man = json.load(open(paths.manifest))
    if change == "benchmark":
        with open(os.path.join(paths.gen, "country_benchmark.csv"), "a", encoding="utf-8") as fh:
            fh.write("\n")
    elif change == "exclusions":
        with open(paths.exclusions, "a", encoding="utf-8") as fh:
            fh.write("\n")
    elif change == "config_hash":
        man["config_sha256"] = "0" * 64
    elif change == "treatments_hash":
        man["review_treatments_sha256"] = "0" * 64
    elif change == "audit":
        man["files"].pop("excluded_items.csv")
    elif change == "approved_by":
        man["approved_by"] = ""
    if change == "no_manifest":
        os.remove(paths.manifest)
    else:
        json.dump(man, open(paths.manifest, "w"))
    with pytest.raises(RunControlError):
        open_run(paths, "synthetic test")
    assert not os.path.exists(paths.runs) and not os.path.exists(paths.log)


def test_open_run_requires_dev_tuning_record_and_authoriser(syn, tmp_path):
    p = make_paths(tmp_path, syn["gen"], syn["path"], syn["pilot"], tuning_split="test")
    with pytest.raises(RunControlError, match="DEV-only"):
        open_run(p, "synthetic test")
    os.remove(p.tuning)
    with pytest.raises(RunControlError, match="tuning record missing"):
        open_run(p, "synthetic test")
    p = make_paths(tmp_path, syn["gen"], syn["path"], syn["pilot"])
    for who in ("", "   ", None):
        with pytest.raises(RunControlError, match="authorised-by"):
            open_run(p, who)


def test_inputs_changed_during_a_run_stop_evaluation(paths):
    run = open_run(paths, "synthetic test")
    with open(os.path.join(paths.gen, "product_benchmark.csv"), "a", encoding="utf-8") as fh:
        fh.write("\n")
    with pytest.raises(RunControlError, match="changed since freezing"):
        evaluate.evaluate(primary_systems(), "test", "primary", run=run)


def test_stage_evaluate_requires_explicit_split_and_authoriser(paths):
    for split, who in (("", "synthetic test"), ("dev", "synthetic test"), ("test", "")):
        with pytest.raises(SystemExit):
            run_all.stage_evaluate({}, split, who, paths=paths)
    assert not os.path.exists(paths.runs)


def test_stage_evaluate_full_route_in_temporary_directories(paths):
    run = run_all.stage_evaluate({}, "test", "synthetic test", paths=paths)
    files = _files(run.run_dir)
    for name in ("run.json", "outputs_sha256.json", "processed/primary_test_product_summary.csv",
                 "processed/ladder_test_paired_tests.csv", "figures/primary_test_product_summary_outcomes.pdf",
                 "figures/figures_provenance.json", "processed/primary_test_excluded_from_metrics.csv"):
        assert name in files, name
    events = [(e["event"], e["run_id"]) for e in read_log(paths.log)]
    assert events == [("started", run.run_id), ("completed", run.run_id)]
    recorded = json.load(open(os.path.join(run.run_dir, "outputs_sha256.json")))
    assert all(recorded[k] == v for k, v in files.items() if k != "outputs_sha256.json")


def test_stage_evaluate_logs_aborted_runs_and_keeps_them(paths, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("synthetic failure")
    monkeypatch.setattr(evaluate, "evaluate", boom)
    with pytest.raises(RuntimeError):
        run_all.stage_evaluate({}, "test", "synthetic test", paths=paths)
    log = read_log(paths.log)
    assert [e["event"] for e in log] == ["started", "aborted"] and "synthetic failure" in log[1]["error"]
    assert os.path.isdir(os.path.join(paths.runs, log[0]["run_id"]))


# ============================================================== C. DEV-only tuning
CFG = {"tuning_rule": "test rule", "tuning_grid": {"product_min_coverage": [0.5, 1.0],
                                                   "product_typo_max_edits": [0, 1], "product_typo_min_len": [5]}}


@pytest.mark.parametrize("mutate", ["test", "missing", "empty", "none", "mixed", "upper"])
def test_tuning_rejects_non_dev_rows(mutate, tmp_path):
    rows = [dict(r) for r in DEV_P]
    if mutate == "test":
        rows = [r for r in SYN_PRODUCT if r["split"] == "test"]
    elif mutate == "missing":
        rows[0].pop("split")
    elif mutate == "empty":
        rows[0]["split"] = ""
    elif mutate == "none":
        rows = []
    elif mutate == "mixed":
        rows = rows + [SYN_PRODUCT[9]]
    elif mutate == "upper":
        rows[0]["split"] = "DEV"
    with pytest.raises(TuningSplitError):
        tuning.tune(CFG, rows=rows, out_path=str(tmp_path / "t.json"))
    assert not (tmp_path / "t.json").exists()


def test_tuning_reads_only_dev_rows_from_a_benchmark_file(syn, tmp_path, monkeypatch):
    seen = []
    real = tuning.resolve_product
    monkeypatch.setattr(tuning, "resolve_product", lambda t, *a: seen.append(t) or real(t, *a))
    real_b = tuning.run_B
    monkeypatch.setattr(tuning, "run_B", lambda t, *a: seen.append(t) or real_b(t, *a))
    s1c, rec = tuning.tune(CFG, gen_dir=syn["gen"], out_path=str(tmp_path / "t.json"))
    dev_texts = {r["text"] for r in SYN_PRODUCT if r["split"] == "dev"}
    assert seen and set(seen) <= dev_texts
    assert rec["split"] == "dev" and rec["n_dev_items_pooled_P1_P7"] == len(DEV_P)
    assert rec["input"].startswith("product_benchmark.csv sha256=")
    saved = json.load(open(tmp_path / "t.json"))
    assert saved["chosen"] == rec["chosen"] and saved["tuning_rule"] == "test rule"
    assert tuning.load_tuned(str(tmp_path / "t.json")) == s1c


def test_tuning_record_is_never_overwritten(tmp_path):
    out = tmp_path / "t.json"
    tuning.tune(CFG, rows=DEV_P, out_path=str(out))
    before = out.read_bytes()
    with pytest.raises(FileExistsError):
        tuning.tune(CFG, rows=DEV_P, out_path=str(out))
    assert out.read_bytes() == before


def test_load_tuned_refuses_non_dev_record(tmp_path):
    p = tmp_path / "t.json"
    p.write_text(json.dumps({"split": "test", "chosen": {}}))
    with pytest.raises(TuningSplitError):
        tuning.load_tuned(str(p))


def _g(cov, k, m, acc, ser):
    return dict(product_min_coverage=cov, product_typo_max_edits=k, product_typo_min_len=m,
                dev_macro_decision_accuracy=acc, dev_macro_silent_error_rate=ser)


def test_selection_rule_feasible_infeasible_and_ties():
    grid = [_g(0.5, 1, 5, 0.90, 0.20), _g(0.75, 1, 5, 0.85, 0.05), _g(1.0, 0, 4, 0.85, 0.05), _g(0.25, 2, 4, 0.95, 0.30)]
    chosen, rule = tuning.select(grid, b_ser=0.10)   # feasible: SER <= 0.10 -> best accuracy, tie -> larger coverage
    assert (chosen["product_min_coverage"], rule) == (1.0, "max dev accuracy s.t. dev SER <= SER(B)")
    chosen, rule = tuning.select(grid, b_ser=0.01)   # infeasible -> minimum SER, reported as such
    assert chosen["dev_macro_silent_error_rate"] == 0.05 and rule.startswith("infeasible")
    assert chosen["product_min_coverage"] == 1.0     # tie on SER and accuracy -> larger coverage threshold


def test_tuning_selection_unchanged_from_pre_declared_procedure(tmp_path):
    """Grid metrics are recomputed independently here: macro over P2-P7 DEV subsets only."""
    from lexitax_v2.product import resolve_product

    from lexeval import scoring
    rows = [dict(r, subset=s) for r, s in zip(DEV_P * 3, ["P2_format", "P5_confusable", "P1_exact",
                                                          "P3_typo", "P8_hs_formal", "P5_confusable"])]
    for i, r in enumerate(rows):
        r["item_id"] = f"syn{i}"
    _, rec = tuning.tune(CFG, rows=rows, out_path=str(tmp_path / "t.json"))
    sel = [r for r in rows if r["subset"] not in ("P1_exact", "P8_hs_formal")]
    for g in rec["grid"]:
        by = {}
        for r in sel:
            res = resolve_product(r["text"], g["product_min_coverage"], g["product_typo_max_edits"],
                                  g["product_typo_min_len"])
            o = scoring.product_outcome(r, {"status": "OK", "prod_hs": res["hs_code"] if res["status"] == "RESOLVED" else None})
            by.setdefault(r["subset"], []).append(o)
        acc = sum(scoring.summarise(v)["decision_accuracy"] for v in by.values()) / len(by)
        assert g["dev_macro_decision_accuracy"] == pytest.approx(acc)
    assert rec["n_dev_items_selection_P2_P7"] == len(sel)


# ============================================================== D. DEV-only latency
LCFG = {"seed": 1, "bootstrap_resamples": 50, "latency": {"warmup_calls": 3, "repetitions": 2}}


def test_latency_refuses_test(syn, tmp_path):
    for fn in (lambda: latency.measure({}, LCFG, split="test", gen_dir=syn["gen"], out_path=str(tmp_path / "l.json")),
               lambda: latency.workloads(syn["gen"], split="test")):
        with pytest.raises(LatencySplitError):
            fn()
    assert not (tmp_path / "l.json").exists()


def test_latency_has_no_fallback_to_test(syn, tmp_path):
    gen = tmp_path / "g"
    gen.mkdir()
    for name, rows in (("product_benchmark.csv", SYN_PRODUCT), ("country_benchmark.csv", SYN_COUNTRY)):
        keep = [r for r in rows if r["split"] == "test"]
        with open(gen / name, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(keep)
    with pytest.raises(LatencySplitError, match="no DEV rows"):
        latency.workloads(str(gen))


def test_latency_times_only_dev_inputs_with_separate_workloads(syn, tmp_path):
    calls = []
    out = latency.measure(_recorder(calls), LCFG, gen_dir=syn["gen"], out_path=str(tmp_path / "l.json"))
    dev_p = {r["text"] for r in DEV_P}
    dev_c = {r["text"] for r in DEV_C}
    seen_p = {a[0] for _, a in calls if a[0] in dev_p}
    seen_c = {a[1] for _, a in calls if a[1] in dev_c}
    assert seen_p == dev_p and seen_c == dev_c
    for _, a in calls:  # every call is either a DEV product input or a DEV country input
        assert a[0] in dev_p or a[1] in dev_c
    for w, n in (("product", len(DEV_P)), ("country", len(DEV_C))):
        wl = out["workloads"][w]
        assert wl["n_items"] == n
        for s in ("B", "S0", "S1"):
            st = wl["systems"][s]
            assert st["calls"] == n * 2
            assert len(st["run_to_run"]["repetition_medians_ms"]) == 2
            assert {"median", "p95", "p99", "mean", "sd"} <= set(st["per_call_ms"])
            assert "bootstrap_ci95_of_median_ms" in st["run_to_run"]
    per_system = len(DEV_P) * 2 + 3 + len(DEV_C) * 2 + 3
    assert len(calls) == 3 * per_system
    assert out["split"] == "dev" and "not independent" in out["interpretation"]
    assert {"python", "cpu_count"} <= set(out["environment"])
    with pytest.raises(FileExistsError):
        latency.measure(_recorder([]), LCFG, gen_dir=syn["gen"], out_path=str(tmp_path / "l.json"))


def test_stage_latency_refuses_test_limits_and_unfrozen(monkeypatch):
    with pytest.raises(SystemExit):  # real benchmark is not frozen
        run_all.stage_latency({"latency": {}})
    monkeypatch.setattr(run_all, "_require_frozen", lambda: {})
    with pytest.raises(SystemExit, match="automated tests only"):
        run_all.stage_latency({"latency": {"max_items_per_workload": 5}})


def test_production_latency_config_is_dev_workloads():
    from lexeval.paths import config
    lat = config()["latency"]
    assert lat["split"] == "dev" and set(lat["workloads"]) == {"product", "country"}
    assert (lat["warmup_calls"], lat["repetitions"]) == (200, 30) and "workload_items" not in lat
    assert "max_items_per_workload" not in lat


# ============================================================== E/F. figures
@pytest.fixture
def dev_outputs(syn, tmp_path):
    tj = tmp_path / "tuning_dev.json"
    s1c, _ = tuning.tune(CFG, gen_dir=syn["gen"], out_path=str(tj))
    dev_dir = tmp_path / "dev"
    evaluate.evaluate(primary_systems(s1c), "dev", "primary", gen_dir=syn["gen"], out_dir=str(dev_dir))
    return dev_dir, tj


def test_dev_risk_coverage_figure_from_dev_outputs(dev_outputs):
    dev_dir, tj = dev_outputs
    made = figures.dev_figures(str(dev_dir), str(tj))
    pdf = dev_dir / "figures" / "dev_risk_coverage.pdf"
    assert pdf.stat().st_size > 0 and made["dev_risk_coverage.pdf"]["split"] == "dev"
    prov = json.load(open(dev_dir / "figures" / "figures_provenance.json"))
    for name, sha in prov["dev_risk_coverage.pdf"]["inputs"].items():
        src = tj if name == "tuning_dev.json" else dev_dir / "processed" / name
        assert _sha(src) == sha   # reproducible from the recorded inputs
    assert not hasattr(figures, "risk_coverage")  # the TEST-grid version is gone


def test_dev_figure_refuses_non_dev_inputs(dev_outputs, tmp_path):
    dev_dir, tj = dev_outputs
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(dict(json.load(open(tj)), split="test")))
    with pytest.raises(FigureInputError):
        figures.dev_figures(str(dev_dir), str(bad))
    items = dev_dir / "processed" / "primary_dev_product_items.csv"
    rows = read_csv(str(items))
    rows[0]["split"] = "test"
    with open(items, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with pytest.raises(FigureInputError, match="split"):
        figures.dev_figures(str(dev_dir), str(tj))


def test_test_figures_inside_run_and_excluded_id_detection(paths):
    run = open_run(paths, "synthetic test")
    evaluate.evaluate(primary_systems(), "test", "primary", run=run)
    items = os.path.join(run.run_dir, "processed", "primary_test_product_items.csv")
    rows = read_csv(items)
    with open(items, "a", encoding="utf-8", newline="") as fh:  # simulate a leaked excluded row
        csv.DictWriter(fh, fieldnames=list(rows[0])).writerow(dict(rows[0], item_id="CE|sint"))
    with pytest.raises(FigureInputError, match="excluded"):
        figures.figures_for_test_run(run)
    assert not os.path.exists(os.path.join(run.run_dir, "figures", "figures_provenance.json"))
    close_run(run, "aborted", error="synthetic leak test")


def test_test_figures_refuse_closed_or_forged_runs(paths, tmp_path):
    forged = AuthorisedTestRun("forged", str(tmp_path), paths, {"evaluation_exclusions_sha256": "x"}, {})
    with pytest.raises(RunControlError):
        figures.figures_for_test_run(forged)
    run = open_run(paths, "synthetic test")
    evaluate.evaluate(primary_systems(), "test", "primary", run=run)
    made = figures.figures_for_test_run(run)
    assert set(made) == {"primary_test_product_summary_outcomes.pdf", "primary_test_identification_summary_outcomes.pdf",
                         "primary_test_tax_behaviour_summary_outcomes.pdf"}
    for name, m in made.items():
        assert m["input_sha256"] == _sha(os.path.join(run.run_dir, "processed", m["input"]))
    close_run(run)
    with pytest.raises(RunControlError):
        figures.figures_for_test_run(run)


# ============================================================== G. ladder evaluation
def test_ladder_pairs_are_adjacent_ladder_steps():
    lad = ladder_systems()
    names = list(lad)[:6]
    assert [n[:2] for n in names] == ["L0", "L1", "L2", "L3", "L4", "L5"]
    assert evaluate.ladder_pairs(lad) == [(names[i], names[i + 1]) for i in range(5)]
    assert all(not n.startswith("L") for n in list(lad)[6:])  # extra ablations are not ladder steps


@pytest.mark.parametrize("sensitivity", [True, False])
def test_ladder_evaluation_in_both_sensitivity_modes(paths, sensitivity):
    lad = ladder_systems()
    run = open_run(paths, "synthetic test")
    prows, crows, _ = evaluate.evaluate(lad, "test", "ladder", pairs=evaluate.ladder_pairs(lad), run=run,
                                        sensitivity=sensitivity)
    close_run(run)
    proc = os.path.join(run.run_dir, "processed")
    n = len(lad)
    assert len(prows) == len(TEST_SCORED_P) * n and len(crows) == len(TEST_SCORED_C) * n
    assert {r["item_id"] for r in prows} == TEST_SCORED_P and {r["item_id"] for r in crows} == TEST_SCORED_C
    assert {r["split"] for r in prows + crows} == {"test"}
    for path in _files(run.run_dir):
        if path.endswith(("excluded_from_metrics.csv", "sensitivity_siblings_info.json")):
            continue
        text = open(os.path.join(run.run_dir, path), encoding="utf-8", errors="ignore").read()
        for needle in list(AUTHORISED) + SENTINELS:
            assert needle not in text, (needle, path)
    summ = read_csv(os.path.join(proc, "ladder_test_product_summary.csv"))
    for s in lad:
        got = {r["subset"]: int(r["n"]) for r in summ if r["system"] == s}
        assert got == {"P1_exact": 3, "P2_format": 2, "P7_outside": 1, "P8_hs_formal": 1, "ALL": 6}, s
    tests = read_csv(os.path.join(proc, "ladder_test_paired_tests.csv"))
    assert len(tests) == 5 * 2 * 3
    assert {int(t["n_items"]) for t in tests if t["task"] == "product"} == {6}
    sens_files = [f for f in os.listdir(proc) if "sensitivity" in f]
    if sensitivity:
        assert "ladder_sensitivity_siblings_removed_test_product_summary.csv" in sens_files
        ss = read_csv(os.path.join(proc, "ladder_sensitivity_siblings_removed_test_product_summary.csv"))
        l5 = list(lad)[5]
        assert {r["subset"]: int(r["n"]) for r in ss if r["system"] == l5}["ALL"] == 3
    else:
        assert sens_files == []
    prov = json.load(open(os.path.join(proc, "ladder_test_provenance.json")))
    assert prov["sensitivity_outputs"] is sensitivity and prov["run_id"] == run.run_id


def test_ladder_dev_evaluation_stays_dev(syn, tmp_path):
    lad = ladder_systems()
    prows, crows, _ = evaluate.evaluate(lad, "dev", "ladder", pairs=evaluate.ladder_pairs(lad), gen_dir=syn["gen"],
                                        out_dir=str(tmp_path / "d"))
    assert {r["item_id"] for r in prows} == {r["item_id"] for r in DEV_P}
    assert {r["split"] for r in prows + crows} == {"dev"}
    assert not [f for f in os.listdir(tmp_path / "d" / "processed") if "excluded" in f or "sensitivity" in f]


# ============================================================== H. permanent TEST run controls
def test_run_records_ids_and_hashes(paths):
    run = open_run(paths, "synthetic test")
    rec = json.load(open(os.path.join(run.run_dir, "run.json")))
    assert rec["run_id"] == run.run_id == os.path.basename(run.run_dir)
    assert len(run.run_id.split("-")[0]) == 16 and run.run_id.split("-")[0].endswith("Z")
    h = rec["hashes"]
    assert set(h) == {"manifest_sha256", "benchmark_files", "config_sha256", "review_treatments_sha256",
                      "evaluation_exclusions_sha256", "tuning_record_sha256", "code_sha256"}
    assert h["evaluation_exclusions_sha256"] == _sha(paths.exclusions)
    assert any(k.endswith("lexeval/evaluate.py") for k in rec["code_files_sha256"])
    assert rec["authorised_by"] == "synthetic test" and rec["previous_runs"] == []
    close_run(run)


def test_rerun_requires_reason_and_keeps_earlier_run(paths):
    first = open_run(paths, "synthetic test")
    evaluate.evaluate(primary_systems(), "test", "primary", run=first)
    close_run(first)
    snapshot = _files(first.run_dir)
    log_before = open(paths.log, "rb").read()
    for reason in (None, "", "  "):
        with pytest.raises(RunControlError, match="rerun-reason"):
            open_run(paths, "synthetic test", rerun_reason=reason)
    with pytest.raises(RunControlError, match="authorised-by"):
        open_run(paths, "", rerun_reason="fix")
    import datetime
    later = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=5)
    second = open_run(paths, "second author", rerun_reason="synthetic rerun", now=later)
    assert second.run_id != first.run_id and second.start_record["previous_runs"] == [first.run_id]
    assert second.start_record["rerun_reason"] == "synthetic rerun"
    close_run(second)
    assert _files(first.run_dir) == snapshot                      # earlier run untouched
    assert open(paths.log, "rb").read().startswith(log_before)    # log only appended
    assert [e["event"] for e in read_log(paths.log)] == ["started", "completed", "started", "completed"]


def test_run_directory_is_never_reused(paths):
    import datetime
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    run = open_run(paths, "synthetic test", now=now)
    close_run(run)
    with pytest.raises(RunControlError, match="already exists"):
        open_run(paths, "synthetic test", rerun_reason="same second", now=now)


def test_outputs_cannot_be_silently_replaced(paths):
    run = open_run(paths, "synthetic test")
    evaluate.evaluate(primary_systems(), "test", "primary", run=run)
    with pytest.raises(FileExistsError):           # same run, same tag: exclusive create refuses
        evaluate.evaluate(primary_systems(), "test", "primary", run=run)
    outputs = close_run(run)
    for rel in outputs:
        mode = os.stat(os.path.join(run.run_dir, rel)).st_mode
        assert not mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH), rel
    with pytest.raises(RunControlError):
        close_run(run)


@pytest.mark.parametrize("tamper", ["edit", "delete_line", "truncate"])
def test_tampered_log_blocks_new_runs(paths, tamper):
    run = open_run(paths, "synthetic test")
    close_run(run)
    lines = open(paths.log, "rb").read().splitlines(keepends=True)
    if tamper == "edit":
        lines[0] = lines[0].replace(b"synthetic test", b"someone else")
    elif tamper == "delete_line":
        lines = lines[1:]
    else:
        lines[-1] = lines[-1].rstrip(b"\n")
    open(paths.log, "wb").write(b"".join(lines))
    with pytest.raises(RunControlError, match="run log"):
        open_run(paths, "synthetic test", rerun_reason="after tamper")


def test_real_repository_has_no_runs_or_manifest():
    assert not os.path.exists(os.path.join(GEN, "MANIFEST.json"))
    assert not os.path.exists(os.path.join(RESULTS, "runs")) and not os.path.exists(os.path.join(RESULTS, "test_runs.jsonl"))
    assert not os.path.exists(os.path.join(RESULTS, "tuning_dev.json"))
    assert not os.path.exists(os.path.join(RESULTS, "latency_dev.json"))
    assert EXP in RESULTS


def test_existing_summary_in_run_is_never_replaced(paths):
    """Each TEST output file is created exclusively: a pre-existing summary stops the evaluation unchanged."""
    run = open_run(paths, "synthetic test")
    proc = os.path.join(run.run_dir, "processed")
    os.makedirs(proc)
    target = os.path.join(proc, "primary_test_product_summary.csv")
    with open(target, "w", encoding="utf-8") as fh:
        fh.write("earlier result\n")
    with pytest.raises(FileExistsError):
        evaluate.evaluate(primary_systems(), "test", "primary", run=run)
    assert open(target, encoding="utf-8").read() == "earlier result\n"
    close_run(run, "aborted", error="synthetic overwrite test")


def test_write_rows_exclusive_refuses_existing_file(tmp_path):
    p = tmp_path / "x.csv"
    evaluate.write_rows(str(p), [{"a": 1}], exclusive=True)
    with pytest.raises(FileExistsError):
        evaluate.write_rows(str(p), [{"a": 2}], exclusive=True)
    assert p.read_text() == "a\n1\n" or p.read_text() == "a\r\n1\r\n"
