"""Latency/throughput measurement (in-process, repeated, warm-up, environment recorded)."""
import json
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


def measure(systems, cfg, split="test"):
    lat = cfg["latency"]
    items = [r for r in read_csv(os.path.join(GEN, "product_benchmark.csv")) if r["split"] == split]
    items = sorted(items, key=lambda r: r["item_id"])[: lat["workload_items"]]
    countries = sorted(ISO_TO_TABLE.values())
    work = [(it["text"], countries[i % len(countries)], 100.0, 2, 10.0) for i, it in enumerate(items)]
    out = {"environment": environment(), "workload_items": len(work), "repetitions": lat["repetitions"],
           "warmup_calls": lat["warmup_calls"], "systems": {}}
    for name, fn in systems.items():
        for i in range(lat["warmup_calls"]):
            fn(*work[i % len(work)])
        samples, rep_medians = [], []
        t_start = time.perf_counter()
        for _ in range(lat["repetitions"]):
            rep = []
            for args in work:
                t0 = time.perf_counter_ns()
                fn(*args)
                rep.append((time.perf_counter_ns() - t0) / 1e6)
            samples.extend(rep)
            rep_medians.append(statistics.median(rep))
        wall = time.perf_counter() - t_start
        s = sorted(samples)
        # CI of the median across repetitions (run-to-run variability)
        lo, hi = bootstrap_ci(rep_medians, statistics.median, cfg["bootstrap_resamples"], cfg["seed"])
        out["systems"][name] = {
            "calls": len(samples), "mean_ms": statistics.fmean(samples), "sd_ms": statistics.pstdev(samples),
            "median_ms": statistics.median(samples), "median_ci95_ms": [lo, hi],
            "p95_ms": s[int(0.95 * len(s)) - 1], "p99_ms": s[int(0.99 * len(s)) - 1],
            "throughput_calls_per_s": len(samples) / wall}
    with open(os.path.join(RESULTS, "latency.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    return out
