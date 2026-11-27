"""Latency/throughput measurement on DEV inputs only (in-process, repeated, warm-up, environment recorded).

Phase C: TEST inputs are refused; product and country workloads are timed and reported separately.
"""
import hashlib
import json
import math
import os
import platform
import statistics
import time

from lexitax_v2.reference import ISO_TO_TABLE

from .build_common import read_csv
from .paths import GEN, RESULTS
from .stats import bootstrap_ci


def environment():
    import importlib.metadata as m
    info = {"python": platform.python_version(), "platform": platform.platform(),
            "processor": platform.processor(), "cpu_count": os.cpu_count()}
    try:
        with open("/proc/cpuinfo") as fh:
            for line in fh:
                if line.startswith("model name"):
                    info["cpu_model"] = line.split(":", 1)[1].strip()
                    break
        with open("/proc/meminfo") as fh:
            info["mem_total"] = fh.readline().split(":", 1)[1].strip()
    except OSError:
        pass
    for pkg in ("flask", "pycountry", "babel", "numpy", "scipy", "matplotlib", "pandas"):
        try:
            info[pkg] = m.version(pkg)
        except m.PackageNotFoundError:
            pass
    return info


def raw_systems(s1_config):
    """Time the systems' own entry points, NOT the evaluation adapters (adapter overhead is not
    part of any system; e.g. the B adapter's category lookup doubles B's apparent latency)."""
    from lexitax_v2 import run_s1
    from lexitax_v2.legacy import server
    srv = server()
    return {
        "B": lambda p, d, pr, q, s: srv.run_normal_auditor_pipeline(p, d, pr, q, s),
        "S0": lambda p, d, pr, q, s: srv.run_agentic_auditor_pipeline(p, d, pr, q, s),
        "S1": lambda p, d, pr, q, s: run_s1({"product_name": p, "destination": d, "price": pr,
                                             "quantity": q, "shipping": s}, s1_config),
    }


class LatencySplitError(ValueError):
    """Latency may only be measured on DEV inputs."""


INTERPRETATION = ("Repeated timings of the same DEV inputs are not independent research examples. Intervals describe "
                  "measurement variability on the recorded machine and workload only, not general performance; "
                  "results are indicative (shared cloud VM).")


def _dev_rows(rows, where):
    if not rows:
        raise LatencySplitError(f"{where}: no DEV rows (there is no fallback to another split)")
    bad = sorted({repr(r.get("split")) for r in rows if r.get("split") != "dev"})
    if bad:
        raise LatencySplitError(f"{where}: only split 'dev' rows may be timed; found {bad}")
    return rows


def workloads(gen_dir=None, split="dev", max_items=None):
    """DEV workloads: every DEV product item (with a canonical table country) and every DEV country item
    (with a canonical catalogue product). TEST is refused; there is no fallback."""
    if split != "dev":
        raise LatencySplitError(f"latency is DEV-only; split {split!r} refused")
    from lexitax_v2.reference import catalogue
    gen_dir = gen_dir or GEN
    prod = _dev_rows(sorted((r for r in read_csv(os.path.join(gen_dir, "product_benchmark.csv"))
                             if r.get("split") == "dev"), key=lambda r: r["item_id"]), "product workload")
    ctry = _dev_rows(sorted((r for r in read_csv(os.path.join(gen_dir, "country_benchmark.csv"))
                             if r.get("split") == "dev"), key=lambda r: r["item_id"]), "country workload")
    if max_items:  # testing only; recorded in the output and refused by run_all
        prod, ctry = prod[:max_items], ctry[:max_items]
    countries = sorted(ISO_TO_TABLE.values())
    products = sorted(catalogue()[1])
    return {"product": [(r["item_id"], (r["text"], countries[i % len(countries)], 100.0, 2, 10.0))
                        for i, r in enumerate(prod)],
            "country": [(r["item_id"], (products[i % len(products)], r["text"], 100.0, 2, 10.0))
                        for i, r in enumerate(ctry)]}


def _pct(sorted_vals, q):
    """Nearest-rank percentile."""
    return sorted_vals[max(0, math.ceil(q * len(sorted_vals)) - 1)]


def _time_workload(fn, work, warmup, reps, cfg):
    for i in range(warmup):
        fn(*work[i % len(work)])
    samples, rep_medians, rep_walls = [], [], []
    t_start = time.perf_counter()
    for _ in range(reps):
        rep, r0 = [], time.perf_counter()
        for args in work:
            t0 = time.perf_counter_ns()
            fn(*args)
            rep.append((time.perf_counter_ns() - t0) / 1e6)
        rep_walls.append(time.perf_counter() - r0)
        samples.extend(rep)
        rep_medians.append(statistics.median(rep))
    wall = time.perf_counter() - t_start
    s, m = sorted(samples), sorted(rep_medians)
    lo, hi = bootstrap_ci(rep_medians, statistics.median, cfg["bootstrap_resamples"], cfg["seed"])
    return {"calls": len(samples), "per_call_ms": {
                "median": statistics.median(s), "p95": _pct(s, 0.95), "p99": _pct(s, 0.99),
                "mean": statistics.fmean(s), "sd": statistics.pstdev(s)},
            "throughput_calls_per_s": len(samples) / wall,
            "run_to_run": {"repetition_medians_ms": rep_medians, "repetition_wall_s": rep_walls,
                           "median_of_repetition_medians_ms": statistics.median(m),
                           "min_ms": m[0], "max_ms": m[-1], "iqr_ms": _pct(m, 0.75) - _pct(m, 0.25),
                           "bootstrap_ci95_of_median_ms": [lo, hi]}}


def measure(systems, cfg, split="dev", gen_dir=None, out_path=None):
    """Time each system separately on the DEV product workload and the DEV country workload.
    Writes results/latency_dev.json (exclusive-create) unless out_path is given."""
    if split != "dev":
        raise LatencySplitError(f"latency is DEV-only; split {split!r} refused")
    lat = cfg["latency"]
    limit = lat.get("max_items_per_workload")
    work = workloads(gen_dir, "dev", limit)
    out = {"split": "dev", "environment": environment(), "interpretation": INTERPRETATION,
           "method": {"warmup_calls": lat["warmup_calls"], "repetitions": lat["repetitions"],
                      "timer": "time.perf_counter_ns per call; whole workload per repetition",
                      "workload_limited_for_testing": bool(limit)},
           "workloads": {}}
    for wname, items in work.items():
        args = [a for _, a in items]
        ids = "\n".join(i for i, _ in items)
        out["workloads"][wname] = {
            "n_items": len(items), "item_ids_sha256": hashlib.sha256(ids.encode()).hexdigest(),
            "systems": {name: _time_workload(fn, args, lat["warmup_calls"], lat["repetitions"], cfg)
                        for name, fn in systems.items()}}
    out_path = out_path or os.path.join(RESULTS, "latency_dev.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "x", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    return out
