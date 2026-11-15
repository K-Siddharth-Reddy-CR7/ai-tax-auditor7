#!/usr/bin/env python3
"""Single entry point for the LEXITAX AUDIT resolution study.

Stages (run in order):
  build     generate DRAFT benchmarks from reference data (deterministic, seeded)
  validate  provenance / duplicate / conflict / leakage checks -> data/generated/VALIDATION_REPORT.md
  pilot     10-item human verification sheet -> pilot/pilot_review_sheet.csv
  smoke     sanity checks on the 400 canonical transactions (no benchmark scoring)
  freeze    hash benchmarks into MANIFEST.json (requires --approved-by, after pilot sign-off)
  tune      select S1 parameters on DEV (requires frozen manifest)
  evaluate  score B/S0/S1 + ladder on TEST, statistics, latency, figures (requires frozen manifest)
"""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lexeval import build_countries, build_malformed, build_products  # noqa: E402
from lexeval.build_common import write_csv  # noqa: E402
from lexeval.paths import EXP, GEN, RESULTS, config  # noqa: E402

MANIFEST = os.path.join(GEN, "MANIFEST.json")
DATA_FILES = ["product_benchmark.csv", "country_benchmark.csv", "malformed_inputs.csv"]


def _sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _require_frozen():
    if not os.path.exists(MANIFEST):
        sys.exit("Benchmarks are not frozen. Complete the pilot review and run --stage freeze --approved-by NAME.")
    man = json.load(open(MANIFEST, encoding="utf-8"))
    for f, h in man["files"].items():
        if _sha(os.path.join(GEN, f)) != h:
            sys.exit(f"Frozen file changed after freezing: {f}")
    return man


def stage_build(cfg):
    if os.path.exists(MANIFEST):
        sys.exit("Benchmarks are frozen; refusing to rebuild (log an erratum instead).")
    log = []
    prods = build_products.build(cfg, log)
    ctrs = build_countries.build(cfg, log)
    write_csv(os.path.join(GEN, "product_benchmark.csv"), prods, build_products.FIELDS)
    write_csv(os.path.join(GEN, "country_benchmark.csv"), ctrs, build_countries.FIELDS)
    write_csv(os.path.join(GEN, "malformed_inputs.csv"), build_malformed.build(), build_malformed.FIELDS)
    with open(os.path.join(GEN, "build_log.json"), "w", encoding="utf-8") as fh:
        json.dump(log, fh, indent=1)
    print(f"built {len(prods)} product items, {len(ctrs)} country items")
    return log


def stage_validate():
    from lexeval.refdata import edition_markers, versions
    from lexeval.validate import validate, write_report
    rep = validate()
    log = json.load(open(os.path.join(GEN, "build_log.json"), encoding="utf-8"))
    rep["stats"]["reference"] = {"hs_edition_markers": edition_markers(), "versions": versions()}
    write_report(rep, log, os.path.join(GEN, "VALIDATION_REPORT.md"))
    print(f"validation: {len(rep['errors'])} errors, {len(rep['warnings'])} warnings")
    return rep


def stage_smoke():
    from lexeval.systems import SRV, ladder_systems, primary_systems, run_composite, run_S0, run_S1
    keys = ("prod_hs", "country_iso", "duty_rate", "gst_rate", "landing_cost", "policy_id")
    n = 0
    for t in SRV.SAMPLE_TRANSACTIONS:
        a = (t["Product"], t["Destination_Country"], t["Unit_Price_USD"], t["Quantity"], t["Shipping_USD"])
        s0, l0 = run_S0(*a), run_composite(*a)  # identical inputs to every system
        assert {k: s0[k] for k in keys} == {k: l0[k] for k in keys}, ("L0 != S0", a)
        s1 = run_S1(*a)
        l5 = run_composite(*a, validate=True, product_mode="s1", country_mode="iso_refuse")
        assert {k: s1[k] for k in keys} == {k: l5[k] for k in keys}, ("L5 != S1", a)
        outs = {name: fn(*a) for name, fn in {**primary_systems(), **ladder_systems()}.items()}
        assert len({o["landing_cost"] for o in outs.values()}) == 1, ("costs differ on canonical input", a)
        n += 1
    print(f"smoke: {n} canonical transactions; L0==S0, L5==S1, all systems agree on landed cost")


def stage_freeze(approved_by):
    if not approved_by:
        sys.exit("--approved-by is required (name of the author who signed off the pilot)")
    man = {"approved_by": approved_by, "files": {f: _sha(os.path.join(GEN, f)) for f in DATA_FILES},
           "config_sha256": _sha(os.path.join(EXP, "config.json"))}
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(man, fh, indent=2)
    print("frozen:", man)


def stage_tune(cfg):
    _require_frozen()
    from lexeval.tuning import tune
    c, rec = tune(cfg)
    print("chosen:", rec["chosen"], rec["rule_applied"])


def stage_evaluate(cfg):
    _require_frozen()
    from lexeval import evaluate, figures, latency
    from lexeval.systems import ladder_systems, primary_systems
    from lexeval.tuning import load_tuned
    s1c = load_tuned()
    evaluate.evaluate(primary_systems(s1c), "test", "primary")
    ladder = ladder_systems(s1c)
    evaluate.evaluate(ladder, "test", "ladder",
                      pairs=[(a, b) for (a, _), (b, _) in zip(
                          [(k, None) for k in list(ladder)[:6]], [(k, None) for k in list(ladder)[1:6]])])
    latency.measure(latency.raw_systems(s1c), cfg)
    figures.ensure_dir()
    print("evaluation complete; see results/processed and results/latency.json")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", required=True,
                    choices=["build", "validate", "pilot", "smoke", "freeze", "tune", "evaluate"])
    ap.add_argument("--approved-by", default="")
    a = ap.parse_args()
    cfg = config()
    os.makedirs(RESULTS, exist_ok=True)
    if a.stage == "build":
        stage_build(cfg)
    elif a.stage == "validate":
        stage_validate()
    elif a.stage == "pilot":
        from lexeval.pilot import build_lookalike_sheet, build_pilot
        rows = build_pilot(cfg["seed"])
        la = build_lookalike_sheet()
        print(f"pilot sheet with {len(rows)} items written; look-alike confirmation sheet with {len(la)} items")
    elif a.stage == "smoke":
        stage_smoke()
    elif a.stage == "freeze":
        stage_freeze(a.approved_by)
    elif a.stage == "tune":
        stage_tune(cfg)
    elif a.stage == "evaluate":
        stage_evaluate(cfg)


if __name__ == "__main__":
    main()
