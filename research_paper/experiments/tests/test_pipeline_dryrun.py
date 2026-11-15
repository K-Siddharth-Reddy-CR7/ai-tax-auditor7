"""Exercises the evaluation code path on a few DEV items (structure only; no numbers are reported)."""
import csv
import os

import pytest

from lexeval import evaluate, figures, latency
from lexeval.build_common import read_csv
from lexeval.paths import GEN
from lexeval.systems import ladder_systems, primary_systems

pytestmark = pytest.mark.skipif(not os.path.exists(os.path.join(GEN, "product_benchmark.csv")),
                                reason="benchmarks not built")


def test_evaluation_code_path(tmp_path, monkeypatch):
    p = [r for r in read_csv(os.path.join(GEN, "product_benchmark.csv")) if r["split"] == "dev"][::300]
    c = [r for r in read_csv(os.path.join(GEN, "country_benchmark.csv")) if r["split"] == "dev"][::100]
    systems = {**primary_systems(), **ladder_systems()}
    prows = evaluate.run_product_task(p, systems)
    crows = evaluate.run_country_task(c, systems)
    mrows = evaluate.run_malformed(evaluate.build_malformed.build(), primary_systems())
    assert len(prows) == len(p) * len(systems) and len(crows) == len(c) * len(systems)
    assert all(r["rejected"] for r in mrows if r["system"] == "S1")
    summ = evaluate.summarise_by(prows, "outcome")
    assert {"coverage_wilson_ci_low", "silent_error_rate_cluster_ci_high", "decision_accuracy", "n_clusters"} <= set(summ[0])
    tests = evaluate.paired_tests(prows, "outcome", [("B", "S0"), ("S0", "S1")], "product")
    assert len(tests) == 4 and all(0 <= t["p_value"] <= 1 and "n_clusters" in t for t in tests)
    out = tmp_path / "summary.csv"
    evaluate.write_rows(str(out), summ)
    monkeypatch.setattr(figures, "FIGURES", str(tmp_path))
    figures.outcome_bars(str(out), str(tmp_path / "f.pdf"), ["ALL"] * 2, "dry run")
    assert (tmp_path / "f.pdf").stat().st_size > 0


def test_latency_code_path(tmp_path, monkeypatch):
    monkeypatch.setattr(latency, "RESULTS", str(tmp_path))
    cfg = {"seed": 1, "bootstrap_resamples": 100,
           "latency": {"warmup_calls": 2, "repetitions": 2, "workload_items": 5}}
    res = latency.measure({"S1": primary_systems()["S1"]}, cfg, split="dev")
    assert res["systems"]["S1"]["calls"] == 10 and "cpu_count" in res["environment"]
