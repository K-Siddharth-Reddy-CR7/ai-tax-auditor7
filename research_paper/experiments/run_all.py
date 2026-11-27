#!/usr/bin/env python3
"""Single entry point for the LEXITAX AUDIT resolution study.

Stages (run in order):
  build     generate DRAFT benchmarks from reference data (deterministic, seeded); P7 review treatments are
            applied ONLY from pilot/authorised_review_treatments_v1.csv; excluded rows -> excluded_items.csv
  validate  provenance / duplicate / conflict / leakage checks -> data/generated/VALIDATION_REPORT.md
  pilot     human review sheets (pilot, P7 look-alikes, P7 plain scan); existing sheets are never overwritten
  smoke     sanity checks on the 400 canonical transactions (no benchmark scoring)
  freeze    hash benchmarks into MANIFEST.json (requires --approved-by, a build that applied the validated
            authoritative review treatments, and a clean git tree; pins the code identity and git commit)
  tune      select S1 parameters on DEV only, then evaluate B/S0/S1 on DEV and draw the DEV risk-coverage
            figure (requires frozen manifest; writes results/tuning_dev.json and results/dev/, never overwritten)
  latency   time B/S0/S1 on the DEV product and DEV country workloads separately (requires frozen manifest
            and tuning record; writes results/latency_dev.json, never overwritten). TEST is never timed
  recover-runs  only if the TEST run history fails reconciliation: --authorised-by NAME --recovery-reason TEXT;
            records an evidence-preserving recovery (nothing is deleted or rewritten)
  evaluate  the ONLY TEST route: --split test --authorised-by NAME [--rerun-reason TEXT]. Verifies the
            manifest, opens a permanent run results/runs/<run_id>/ logged in results/test_runs.jsonl, scores
            B/S0/S1 and the ladder on exclusion-filtered TEST rows, and draws the TEST figures in the run
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
    """Verify every hash in the freeze manifest (benchmarks, audit file, config, decisions, exclusions)."""
    from lexeval.run_control import RunControlError, RunPaths, verify_manifest
    try:
        return verify_manifest(RunPaths(gen=GEN, manifest=MANIFEST))
    except RunControlError as e:
        sys.exit(f"Refused: {e}")


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


def freeze_preconditions(gen_dir=None, pilot_dir=None, exclusions_path=None):
    """Return a list of reasons the benchmark may NOT be frozen (empty list = review treatments verified).

    Checks the authoritative decisions file against the review records, and that the generated benchmark,
    excluded_items.csv and build_log.json all reflect exactly that file. The scan file's REVIEWED line is
    deliberately not consulted."""
    from lexeval.build_common import read_csv
    from lexeval.pilot import (LOOKALIKE_FILE, PLAIN_PROGRESS_FILE, TREATMENTS_FILE, ReviewTreatmentError,
                               load_treatments, sha256_file)
    from lexeval.eval_exclusions import EvaluationExclusionError, load_exclusions
    gen_dir, pilot_dir = gen_dir or GEN, pilot_dir or PILOT
    try:
        tre = load_treatments(pilot_dir=pilot_dir)
    except ReviewTreatmentError as e:
        return [f"decisions file invalid: {e}"]
    try:  # Phase B: the TEST evaluation exclusions must be valid against this benchmark
        load_exclusions(exclusions_path, gen_dir=gen_dir, pilot_dir=pilot_dir)
    except (EvaluationExclusionError, FileNotFoundError) as e:
        return [f"evaluation exclusions invalid: {e}"]
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


def stage_freeze(approved_by, paths=None):
    """Write MANIFEST.json: benchmark, audit, config, decisions and exclusion hashes plus the code identity and
    git commit (clean working tree required). Never overwrites an existing manifest."""
    if not approved_by:
        sys.exit("--approved-by is required (name of the author who signed off the pilot)")
    problems = freeze_preconditions()
    if problems:
        sys.exit("Freeze refused:\n- " + "\n- ".join(problems))
    from lexeval.run_control import RunControlError, RunPaths, manifest_record
    paths = paths or RunPaths(gen=GEN, manifest=MANIFEST)
    try:
        man = manifest_record(paths, approved_by)
    except RunControlError as e:
        sys.exit(f"Freeze refused: {e}")
    try:
        with open(paths.manifest, "x", encoding="utf-8") as fh:
            json.dump(man, fh, indent=2, sort_keys=True)
    except FileExistsError:
        sys.exit("Freeze refused: MANIFEST.json already exists (a freeze is never overwritten).")
    print("frozen:", {k: v for k, v in man.items() if k != "code_identity"},
          "code", man["code_identity"]["sha256"][:12], "commit", man["code_identity"]["git_commit"][:12])


def stage_tune(cfg):
    """DEV only: select S1's parameters, evaluate B/S0/S1 on DEV, draw the DEV risk-coverage figure."""
    _require_frozen()
    from lexeval import evaluate, figures
    from lexeval.systems import primary_systems
    from lexeval.tuning import tune
    tuning_json, dev_dir = os.path.join(RESULTS, "tuning_dev.json"), os.path.join(RESULTS, "dev")
    if os.path.exists(tuning_json) or os.path.exists(dev_dir):
        sys.exit("Refused: DEV tuning outputs already exist; they are never overwritten.")
    s1c, rec = tune(cfg, out_path=tuning_json)
    evaluate.evaluate(primary_systems(s1c), "dev", "primary", out_dir=dev_dir)
    grid_json = os.path.join(dev_dir, "grid_full_pipeline_dev.json")
    from lexeval.tuning import full_pipeline_grid
    full_pipeline_grid(cfg, rec, out_path=grid_json)  # figure/sensitivity only; selection is unchanged
    figures.dev_figures(dev_dir, tuning_json, grid_json)
    print("chosen:", rec["chosen"], rec["rule_applied"])


def stage_latency(cfg):
    """DEV only: product and country workloads timed separately for the raw B, S0 and tuned S1 entry points."""
    _require_frozen()
    from lexeval import latency
    from lexeval.tuning import load_tuned
    if cfg["latency"].get("max_items_per_workload"):
        sys.exit("Refused: max_items_per_workload is for automated tests only.")
    res = latency.measure(latency.raw_systems(load_tuned()), cfg)
    print("latency (DEV):", {k: v["n_items"] for k, v in res["workloads"].items()})


def stage_evaluate(cfg, split="", authorised_by="", rerun_reason="", paths=None):
    """The only authorised TEST route. Every hash is verified from the frozen manifest by open_run; nothing is
    taken from the caller. Outputs go to a new permanent run directory; the run log is append-only."""
    if split != "test":
        sys.exit("Refused: TEST evaluation requires an explicit --split test.")
    from lexeval import evaluate, figures
    from lexeval.run_control import RunControlError, RunPaths, close_run, open_run
    from lexeval.systems import ladder_systems, primary_systems
    from lexeval.tuning import load_tuned
    paths = paths or RunPaths(gen=GEN, manifest=MANIFEST)
    try:
        run = open_run(paths, authorised_by, rerun_reason)
    except RunControlError as e:
        sys.exit(f"Refused: {e}")
    try:
        s1c = load_tuned(paths.tuning, expected_sha256=run.start_record["hashes"]["tuning_record_sha256"])
        evaluate.evaluate(primary_systems(s1c), "test", "primary", run=run)
        ladder = ladder_systems(s1c)
        evaluate.evaluate(ladder, "test", "ladder", pairs=evaluate.ladder_pairs(ladder), run=run)
        figures.figures_for_test_run(run)
    except BaseException as e:
        try:
            close_run(run, "aborted", error=f"evaluation failed: {type(e).__name__}: {e}")
        except RunControlError as ce:
            # The run is recorded as aborted with both errors in close.json; the original evaluation error is
            # re-raised and keeps the close-time failure as a note (neither error hides the other).
            e.add_note(f"additionally, the close-time integrity check failed: {ce}")
        raise
    try:
        close_run(run, "completed")
    except RunControlError as e:
        sys.exit(f"TEST run closed as aborted: {e}")
    print(f"TEST run {run.run_id} complete: {run.run_dir}")
    return run


def stage_recover_runs(authorised_by="", reason="", paths=None):
    """Authorised, evidence-preserving acknowledgement of an inconsistent TEST run history."""
    from lexeval.run_control import RunControlError, RunPaths, recover
    try:
        rec = recover(paths or RunPaths(gen=GEN, manifest=MANIFEST), authorised_by, reason)
    except RunControlError as e:
        sys.exit(f"Recovery refused: {e}")
    print(f"recovery {rec['recovery_id']} recorded; {len(rec['problems'])} problem(s) acknowledged")
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", required=True,
                    choices=["build", "validate", "pilot", "smoke", "freeze", "tune", "latency", "evaluate",
                             "recover-runs"])
    ap.add_argument("--approved-by", default="", help="freeze: author who approved the freeze")
    ap.add_argument("--split", default="", help="evaluate: must be 'test'")
    ap.add_argument("--authorised-by", default="", help="evaluate: who authorised this TEST run")
    ap.add_argument("--rerun-reason", default="", help="evaluate: required for any TEST run after the first")
    ap.add_argument("--recovery-reason", default="", help="recover-runs: why the inconsistent history is acknowledged")
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
    elif a.stage == "latency":
        stage_latency(cfg)
    elif a.stage == "evaluate":
        stage_evaluate(cfg, a.split, a.authorised_by, a.rerun_reason)
    elif a.stage == "recover-runs":
        stage_recover_runs(a.authorised_by, a.recovery_reason)


if __name__ == "__main__":
    main()
