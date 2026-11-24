#!/usr/bin/env python3
"""Single entry point for the LEXITAX AUDIT resolution study.

Stages (run in order):
  build     generate DRAFT benchmarks from reference data (deterministic, seeded); P7 review treatments are
            applied ONLY from pilot/authorised_review_treatments_v1.csv; excluded rows -> excluded_items.csv
  validate  provenance / duplicate / conflict / leakage checks -> data/generated/VALIDATION_REPORT.md
  pilot     human review sheets (pilot, P7 look-alikes, P7 plain scan); existing sheets are never overwritten
  smoke     sanity checks on the 400 canonical transactions (no benchmark scoring)
  freeze    hash benchmarks into MANIFEST.json (requires --approved-by and a build that applied the validated
            authoritative review treatments; see freeze_preconditions)
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
from lexeval.paths import EXP, GEN, PILOT, RESULTS, config  # noqa: E402

MANIFEST = os.path.join(GEN, "MANIFEST.json")
DATA_FILES = ["product_benchmark.csv", "country_benchmark.csv", "malformed_inputs.csv"]
EXCLUDED_FILE = "excluded_items.csv"  # audit file: full original rows of authorised review exclusions


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
    log, audit = [], []
    prods = build_products.build(cfg, log, audit=audit)  # aborts on an invalid decisions file
    ctrs = build_countries.build(cfg, log)
    write_csv(os.path.join(GEN, "product_benchmark.csv"), prods, build_products.FIELDS)
    write_csv(os.path.join(GEN, EXCLUDED_FILE), audit, build_products.EXCLUDED_FIELDS)
    write_csv(os.path.join(GEN, "country_benchmark.csv"), ctrs, build_countries.FIELDS)
    write_csv(os.path.join(GEN, "malformed_inputs.csv"), build_malformed.build(), build_malformed.FIELDS)
    with open(os.path.join(GEN, "build_log.json"), "w", encoding="utf-8") as fh:
        json.dump(log, fh, indent=1)
    print(f"built {len(prods)} product items, {len(ctrs)} country items; {len(audit)} review exclusions")
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


def freeze_preconditions(gen_dir=None, pilot_dir=None):
    """Return a list of reasons the benchmark may NOT be frozen (empty list = review treatments verified).

    Checks the authoritative decisions file against the review records, and that the generated benchmark,
    excluded_items.csv and build_log.json all reflect exactly that file. The scan file's REVIEWED line is
    deliberately not consulted."""
    from lexeval.build_common import read_csv
    from lexeval.pilot import (LOOKALIKE_FILE, PLAIN_PROGRESS_FILE, TREATMENTS_FILE, ReviewTreatmentError,
                               load_treatments, sha256_file)
    gen_dir, pilot_dir = gen_dir or GEN, pilot_dir or PILOT
    try:
        tre = load_treatments(pilot_dir=pilot_dir)
    except ReviewTreatmentError as e:
        return [f"decisions file invalid: {e}"]
    excl = {i for i, t in tre.items() if t["authorised_treatment"] == "exclude"}
    keep = set(tre) - excl
    problems = []
    prod_path, audit_path = os.path.join(gen_dir, "product_benchmark.csv"), os.path.join(gen_dir, EXCLUDED_FILE)
    log_path = os.path.join(gen_dir, "build_log.json")
    for p in (prod_path, audit_path, log_path):
        if not os.path.exists(p):
            problems.append(f"missing {os.path.basename(p)} (rebuild with the authoritative decisions file)")
    if problems:
        return problems
    prod = read_csv(prod_path)
    p7 = [r["item_id"] for r in prod if r["subset"] == "P7_outside"]
    if sorted(p7) != sorted(keep):
        problems.append(f"benchmark P7 items differ from the 'keep' decisions: still present "
                        f"{sorted(set(p7) & excl)}, missing {sorted(keep - set(p7))}, "
                        f"unexpected {sorted(set(p7) - set(tre))}, duplicated {len(p7) - len(set(p7))}")
    if excl & {r["item_id"] for r in prod}:
        problems.append("an excluded item is still in product_benchmark.csv")
    audit = read_csv(audit_path)
    if sorted(r["item_id"] for r in audit) != sorted(excl):
        problems.append(f"{EXCLUDED_FILE} must list exactly the authorised exclusions {sorted(excl)}")
    for r in audit:
        t = tre.get(r["item_id"])
        if t is None:
            continue
        want = {"exclusion_reason": t["reason"], "decision_source": t["review_file"],
                "review_item_no": t["review_item_no"], "recorded_decision": t["recorded_decision"],
                "authorised_by": t["authorised_by"], "authorised_on": t["authorised_on"],
                "authorisation_record": t["authorisation_record"], "text": t["text"], "split": t["split"],
                "subset": "P7_outside"}
        bad = [k for k, v in want.items() if r.get(k) != v]
        if bad:
            problems.append(f"{EXCLUDED_FILE}: {r['item_id']} disagrees with the decisions file on {bad}")
    log = [tuple(e) for e in json.load(open(log_path, encoding="utf-8"))]
    expected_prov = {
        ("review_treatments_file", f"{TREATMENTS_FILE} sha256={sha256_file(os.path.join(pilot_dir, TREATMENTS_FILE))}"),
        ("review_record", f"{LOOKALIKE_FILE} sha256={sha256_file(os.path.join(pilot_dir, LOOKALIKE_FILE))}"),
        ("review_record", f"{PLAIN_PROGRESS_FILE} sha256={sha256_file(os.path.join(pilot_dir, PLAIN_PROGRESS_FILE))}"),
    }
    prov = {e for e in log if e[0] in ("review_treatments_file", "review_record")}
    if prov != expected_prov:
        problems.append("build_log.json does not record the current decisions file and review records "
                        "(the benchmark was built from different review inputs; rebuild)")
    logged = sorted(e[1].split(" | ", 1)[0] for e in log if e[0] == "review_exclusion")
    if logged != sorted(excl):
        problems.append(f"build_log.json review_exclusion entries {logged} != authorised exclusions {sorted(excl)}")
    return problems


def stage_freeze(approved_by):
    if not approved_by:
        sys.exit("--approved-by is required (name of the author who signed off the pilot)")
    problems = freeze_preconditions()
    if problems:
        sys.exit("Freeze refused:\n- " + "\n- ".join(problems))
    from lexeval.pilot import TREATMENTS_FILE
    man = {"approved_by": approved_by,
           "files": {f: _sha(os.path.join(GEN, f)) for f in DATA_FILES + [EXCLUDED_FILE]},
           "review_treatments_sha256": _sha(os.path.join(PILOT, TREATMENTS_FILE)),
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
        from lexeval.pilot import build_lookalike_sheet, build_pilot, build_plain_scan_sheet
        rows = build_pilot(cfg["seed"])
        la = build_lookalike_sheet()
        pl = build_plain_scan_sheet()
        print(f"pilot: {len(rows)} items; look-alike review: {len(la)} items; plain-name scan: {len(pl)} names "
              "(existing sheets are never overwritten)")
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
