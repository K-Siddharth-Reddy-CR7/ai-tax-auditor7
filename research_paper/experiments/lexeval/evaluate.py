"""Run systems on the frozen benchmarks and score them (raw -> processed results).

TEST rows are obtained ONLY through eval_exclusions.load_test_items() (the Phase B choke point), which
removes the pilot-inspected items listed in evaluation_exclusions_v1.json. Every metric function below also
calls eval_exclusions.assert_no_excluded(), so an excluded item cannot reach a TEST metric by another path.

Phase C: TEST evaluation requires an authorised run handle from run_control.open_run() (created only by
`run_all.py --stage evaluate`). The exclusion hash comes from the verified freeze manifest, never from the
caller. The per-item scoring functions refuse TEST rows outside such a run and refuse excluded IDs always.
TEST outputs go to the run's own directory and are written with exclusive-create (never overwritten).
"""
import csv
import json
import os
from collections import defaultdict

from lexitax_v2.reference import ISO_TO_TABLE, catalogue, tax_rows_by_iso

from . import build_malformed, eval_exclusions, run_control, scoring
from .build_common import read_csv
from .paths import GEN, RESULTS
from .stats import cluster_bootstrap_ci, cluster_paired_test, holm, mcnemar_exact, wilson
from .paths import config
from .systems import SRV

TABLE_COUNTRIES = sorted(ISO_TO_TABLE.values())


def _numerics(i):
    t = SRV.SAMPLE_TRANSACTIONS[i % len(SRV.SAMPLE_TRANSACTIONS)]
    return t["Unit_Price_USD"], t["Quantity"], t["Shipping_USD"]


def _reference_cost(price, qty, ship, iso):
    row = tax_rows_by_iso()[iso]
    d = SRV.calculation_agent({"price": float(price), "quantity": int(qty), "shipping": float(ship),
                               "duty_rate": float(row["Default_Import_Duty_Percent"]),
                               "gst_rate": float(row["GST_VAT_Percent"]), "currency": row["Currency"]})
    return (float(row["Default_Import_Duty_Percent"]), float(row["GST_VAT_Percent"])), d["landing_cost"]


def _reference_policy(table_country, category):
    d = SRV.rag_policy_agent({"destination": table_country, "category": category})
    rp = d.get("retrieved_policies") or []
    return rp[0].get("Policy_ID") if rp else None


def load(split, run=None, gen_dir=None):
    """Return (product rows, country rows, malformed items, TestItems or None).

    TEST rows come only from the exclusion choke point inside an authorised run (exclusion hash taken from
    the verified manifest). DEV rows are read directly; every excluded item is a TEST item."""
    m = build_malformed.build()  # in-memory: preserves Python types (str vs float) of malformed values
    if split == "test":
        run = run_control.require_run(run)
        ts = eval_exclusions.load_test_items(run.exclusions_sha256, gen_dir=run.paths.gen,
                                             path=run.paths.exclusions, pilot_dir=run.paths.pilot)
        return ts.product, ts.country, m, ts
    if split != "dev":
        raise ValueError(f"unknown split {split!r}")
    if run is not None:
        raise run_control.RunControlError("a TEST run handle must not be used for DEV evaluation")
    gen_dir = gen_dir or GEN
    p = [r for r in read_csv(os.path.join(gen_dir, "product_benchmark.csv")) if r["split"] == split]
    c = [r for r in read_csv(os.path.join(gen_dir, "country_benchmark.csv")) if r["split"] == split]
    return p, c, m, None


def check_items(items, where, run=None, exclusions_path=None):
    """Guard for every per-item scoring function: no excluded ID ever; every row must carry split dev or
    test; TEST rows only inside a verified authorised run."""
    eval_exclusions.assert_no_excluded(items, where, exclusions_path)
    splits = {str(it.get("split", "")) for it in items}
    if not splits <= {"dev", "test"}:
        raise ValueError(f"{where}: every benchmark row must carry split 'dev' or 'test' (got {sorted(splits)})")
    if "test" in splits:
        run_control.require_run(run)


def _classify_propagation(ref, out, id_wrong):
    computed = out["landing_cost"] is not None
    flagged = out["status"] != "OK" or bool(out["flags"])
    if ref is None:
        if not computed:
            return "EXPLICIT_REFUSAL", flagged, None
        return ("COMPUTED_WHEN_SHOULD_REFUSE_FLAGGED" if flagged else "COMPUTED_WHEN_SHOULD_REFUSE_SILENT"), flagged, None
    if not computed:
        return "OVER_REFUSAL", flagged, None
    rel = abs(out["landing_cost"] - ref["landing_cost"]) / ref["landing_cost"]
    if rel > 1e-12:
        return ("FINANCIAL_ERROR_FLAGGED" if flagged else "FINANCIAL_ERROR_SILENT"), flagged, rel
    if id_wrong:
        return ("MASKED_FLAGGED" if flagged else "MASKED_SILENT"), flagged, 0.0
    return "NO_ERROR", flagged, 0.0


def run_product_task(items, systems, raw_fh=None, run=None, exclusions_path=None):
    check_items(items, "run_product_task", run, exclusions_path)
    _, bases = catalogue()
    hs_to_cats = defaultdict(set)
    for b in bases.values():
        hs_to_cats[b["hs"]].add(b["category"])
    rows = []
    for i, it in enumerate(items):
        country = TABLE_COUNTRIES[i % len(TABLE_COUNTRIES)]
        iso = {v: k for k, v in ISO_TO_TABLE.items()}[country]
        price, qty, ship = _numerics(i)
        if it["expected"] == "ANSWER":
            rates, lc = _reference_cost(price, qty, ship, iso)
            cats = hs_to_cats.get(it["label_hs"], set())
            ref = {"landing_cost": lc, "rates": rates,
                   "policy_id": _reference_policy(country, next(iter(cats))) if len(cats) == 1 else None}
        else:
            ref = None
        for name, fn in systems.items():
            out = fn(it["text"], country, price, qty, ship)
            outcome = scoring.product_outcome(it, out)
            id_wrong = out["prod_hs"] != (it["label_hs"] or None)
            prop, flagged, rel = _classify_propagation(ref, out, id_wrong)
            policy_wrong = (ref is not None and ref["policy_id"] is not None and out["policy_id"] is not None
                            and out["policy_id"] != ref["policy_id"])
            row = dict(task="product", item_id=it["item_id"], split=it["split"], subset=it["subset"],
                       cluster=it["cluster"],
                       look_alike=it.get("look_alike", ""), system=name,
                       outcome=outcome, fabricated=out["prod_fabricated"], prod_hs=out["prod_hs"],
                       label_hs=it["label_hs"], expected=it["expected"], propagation=prop,
                       flagged=flagged, rel_cost_error=rel, policy_wrong=policy_wrong)
            rows.append(row)
            if raw_fh:
                raw_fh.write(json.dumps({"row": row, "output": out}, default=str) + "\n")
    return rows


def run_country_task(items, systems, raw_fh=None, run=None, exclusions_path=None):
    check_items(items, "run_country_task", run, exclusions_path)
    _, bases = catalogue()
    base_names = sorted(bases)
    rows = []
    for i, it in enumerate(items):
        bname = base_names[i % len(base_names)]
        price, qty, ship = _numerics(i)
        iso = it["gold_iso"] or None
        if iso and iso in ISO_TO_TABLE:
            rates, lc = _reference_cost(price, qty, ship, iso)
            ref = {"landing_cost": lc, "rates": rates,
                   "policy_id": _reference_policy(ISO_TO_TABLE[iso], bases[bname]["category"])}
        else:
            rates, ref = None, None
        for name, fn in systems.items():
            out = fn(bname, it["text"], price, qty, ship)
            ident = scoring.identification_outcome(it, out)
            beh, sub = scoring.tax_behaviour_outcome(it, out, rates)
            prop, flagged, rel = _classify_propagation(ref, out, out["country_iso"] != iso)
            row = dict(task="country", item_id=it["item_id"], split=it["split"], subset=it["subset"],
                       cluster=it["cluster"],
                       s1_builtin=it["s1_builtin"], system=name,
                       identification=ident, tax_behaviour=beh, tax_subtype=sub,
                       gold_iso=it["gold_iso"], gold_tax_action=it["gold_tax_action"],
                       system_iso=out["country_iso"], identification_safe=scoring.is_safe(ident),
                       tax_behaviour_safe=scoring.is_safe(beh),
                       tax_data_available=it["tax_data_available"], default_rates=out["default_rates"],
                       fx_substituted=out["fx_substituted"], propagation=prop, flagged=flagged,
                       rel_cost_error=rel, product_answered=out["prod_hs"] is not None)
            rows.append(row)
            if raw_fh:
                raw_fh.write(json.dumps({"row": row, "output": out}, default=str) + "\n")
    return rows


def run_malformed(items, systems):
    rows = []
    for it in items:
        args = (it["product_name"], it["destination"], it["price"], it["quantity"], it["shipping"])
        for name, fn in systems.items():
            out = fn(*args)
            rows.append(dict(task="malformed", item_id=it["item_id"], system=name, status=out["status"],
                             rejected=out["status"] in ("INVALID", "ERROR"),
                             computed=out["landing_cost"] is not None, landing_cost=out["landing_cost"]))
    return rows


def summarise_by(rows, key_outcome, group_keys=("system", "subset"), pooled_filter=None, exclusions_path=None):
    """Per (system, subset) summaries. The pooled 'ALL' row includes only rows passing pooled_filter
    (e.g. excludes S1-built-in country forms and the separate formal-HS category)."""
    eval_exclusions.assert_no_excluded(rows, "summarise_by", exclusions_path)
    cfg = config()
    groups = defaultdict(list)
    for r in rows:
        groups[tuple(r[k] for k in group_keys)].append(r)
        if pooled_filter is None or pooled_filter(r):
            groups[tuple(r[k] if k == "system" else "ALL" for k in group_keys)].append(r)
    out = []
    for g, grp in sorted(groups.items()):
        outcomes = [r[key_outcome] for r in grp]
        clusters = [r["cluster"] for r in grp]
        s = scoring.summarise(outcomes)
        for metric, pred in (("silent_error_rate", lambda o: o == scoring.SILENT),
                             ("decision_accuracy", lambda o: o in (scoring.CORRECT, scoring.SAFE)),
                             ("coverage", lambda o: o in (scoring.CORRECT, scoring.SILENT))):
            lo, hi = cluster_bootstrap_ci([pred(o) for o in outcomes], clusters, cfg["bootstrap_resamples"] // 5, cfg["seed"])
            s[f"{metric}_cluster_ci_low"], s[f"{metric}_cluster_ci_high"] = lo, hi
        s["n_clusters"] = len(set(clusters))
        for metric, k in (("coverage", "answered"), ("decision_accuracy", None), ("silent_error_rate", scoring.SILENT)):
            num = s["answered"] if metric == "coverage" else (
                s[scoring.CORRECT] + s[scoring.SAFE] if metric == "decision_accuracy" else s[scoring.SILENT])
            lo, hi = wilson(num, s["n"])
            s[f"{metric}_wilson_ci_low"], s[f"{metric}_wilson_ci_high"] = lo, hi  # item-level (assumes independence)
        out.append(dict(zip(group_keys, g), **s))
    return out


def paired_tests(rows, key_outcome, pairs, task, row_filter=None, exclusions_path=None):
    """Primary: cluster-level sign-flip permutation test + cluster bootstrap CI of the difference.
    Secondary: item-level exact McNemar (assumes independent items; reported for reference only)."""
    eval_exclusions.assert_no_excluded(rows, "paired_tests", exclusions_path)
    cfg = config()
    by_sys = defaultdict(dict)
    cluster_of = {}
    for r in rows:
        if row_filter is None or row_filter(r):
            by_sys[r["system"]][r["item_id"]] = r[key_outcome]
            cluster_of[r["item_id"]] = r["cluster"]
    tests = []
    for a, b in pairs:
        ids = sorted(set(by_sys[a]) & set(by_sys[b]))
        clusters = [cluster_of[i] for i in ids]
        for indicator, pred in (("decision_correct", lambda o: o in (scoring.CORRECT, scoring.SAFE)),
                                ("silent_error", lambda o: o == scoring.SILENT)):
            xa = [pred(by_sys[a][i]) for i in ids]
            xb = [pred(by_sys[b][i]) for i in ids]
            diff, lo, hi, p_cl, ncl = cluster_paired_test(xa, xb, clusters, cfg["statistics"]["permutations"], cfg["seed"])
            n01, n10, p_mc = mcnemar_exact(xa, xb)
            tests.append(dict(task=task, metric=indicator, system_a=a, system_b=b, n_items=len(ids),
                              n_clusters=ncl, rate_a=sum(xa) / len(ids), rate_b=sum(xb) / len(ids),
                              diff_b_minus_a=diff, diff_ci_low=lo, diff_ci_high=hi, p_value=p_cl,
                              mcnemar_a_false_b_true=n01, mcnemar_a_true_b_false=n10, mcnemar_p_item_level=p_mc))
    return tests


def write_rows(path, rows, exclusive=False):
    """Write rows as CSV. exclusive=True (all TEST outputs) refuses to replace an existing file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not rows:
        return
    fields = list(rows[0].keys())
    with open(path, "x" if exclusive else "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def ladder_pairs(ladder):
    """Adjacent attribution-ladder comparisons L0-L1, ..., L4-L5 (the first six ladder systems)."""
    names = list(ladder)[:6]
    return list(zip(names[:-1], names[1:]))


def _metrics(prows, crows, tag, split, pairs, proc, exclusions_path, exclusive):
    """All summary metrics and paired tests for one row set (primary or sensitivity)."""
    realistic = lambda r: r["subset"] != "P8_hs_formal"  # noqa: E731  (formal HS texts reported separately)
    held_out = lambda r: str(r["s1_builtin"]) != "True"  # noqa: E731  (S1-built-in forms excluded from pooled claims)
    ex = exclusions_path
    write_rows(os.path.join(proc, f"{tag}_{split}_product_summary.csv"),
               summarise_by(prows, "outcome", pooled_filter=realistic, exclusions_path=ex), exclusive)
    write_rows(os.path.join(proc, f"{tag}_{split}_identification_summary.csv"),
               summarise_by(crows, "identification", pooled_filter=held_out, exclusions_path=ex), exclusive)
    write_rows(os.path.join(proc, f"{tag}_{split}_tax_behaviour_summary.csv"),
               summarise_by(crows, "tax_behaviour", pooled_filter=held_out, exclusions_path=ex), exclusive)
    if pairs:
        tests = (paired_tests(prows, "outcome", pairs, "product", realistic, ex)
                 + paired_tests(crows, "identification", pairs, "identification", held_out, ex)
                 + paired_tests(crows, "tax_behaviour", pairs, "tax_behaviour", held_out, ex))
        for t, adj in zip(tests, holm([t["p_value"] for t in tests])):
            t["p_holm"] = adj  # Holm over the cluster-level permutation p-values (within this family)
        write_rows(os.path.join(proc, f"{tag}_{split}_paired_tests.csv"), tests, exclusive)


def _write_json(path, obj, exclusive):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "x" if exclusive else "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)


def evaluate(systems, split="test", tag="primary", pairs=(("B", "S0"), ("S0", "S1"), ("B", "S1")),
             run=None, gen_dir=None, out_dir=None, sensitivity=None):
    """Score `systems` on `split`.

    TEST: `run` must be an open authorised run (run_control.open_run, i.e. run_all.py --stage evaluate). The
    exclusion hash comes from its verified manifest; outputs go to the run directory, exclusive-create only.
    With `sensitivity` (default: on for tag 'primary') the sibling-cluster sensitivity outputs are written
    separately. DEV: no run; outputs go to `out_dir` (default results/dev)."""
    p_items, c_items, m_items, ts = load(split, run, gen_dir)
    if ts is not None:
        exclusions_path, out, exclusive = run.paths.exclusions, run.run_dir, True
        eval_exclusions.assert_no_excluded(p_items + c_items, "evaluate(test) inputs", exclusions_path)
    else:
        exclusions_path, out, exclusive = None, out_dir or os.path.join(RESULTS, "dev"), False
    raw_dir, proc = os.path.join(out, "raw"), os.path.join(out, "processed")
    os.makedirs(raw_dir, exist_ok=True)
    with open(os.path.join(raw_dir, f"{tag}_{split}_outputs.jsonl"), "x" if exclusive else "w", encoding="utf-8") as fh:
        prows = run_product_task(p_items, systems, fh, run, exclusions_path)
        crows = run_country_task(c_items, systems, fh, run, exclusions_path)
    mrows = run_malformed(m_items, systems)
    if ts is not None:
        eval_exclusions.assert_no_excluded(prows + crows, "evaluate(test) item rows", exclusions_path)
        eval_exclusions.write_audit(os.path.join(proc, f"{tag}_{split}_excluded_from_metrics.csv"), ts.excluded,
                                    exclusive=True)
    write_rows(os.path.join(proc, f"{tag}_{split}_product_items.csv"), prows, exclusive)
    write_rows(os.path.join(proc, f"{tag}_{split}_country_items.csv"), crows, exclusive)
    write_rows(os.path.join(proc, f"{tag}_{split}_malformed_items.csv"), mrows, exclusive)
    _metrics(prows, crows, tag, split, pairs, proc, exclusions_path, exclusive)
    sens = ts is not None and (tag == "primary" if sensitivity is None else sensitivity)
    if sens:
        # Secondary sensitivity analysis: additionally drop the pre-declared sibling clusters.
        sp = eval_exclusions.without_sibling_clusters(prows, ts.sibling_clusters("product"))
        sc = eval_exclusions.without_sibling_clusters(crows, ts.sibling_clusters("country"))
        n_sys = max(len(systems), 1)
        info = {"definition": ts.spec["sensitivity_sibling_clusters"]["definition"],
                "exclusions_sha256": ts.sha256,
                "product_clusters": sorted(ts.sibling_clusters("product")),
                "country_clusters": sorted(ts.sibling_clusters("country")),
                "product_sibling_items_removed": (len(prows) - len(sp)) // n_sys,
                "country_sibling_items_removed": (len(crows) - len(sc)) // n_sys}
        _write_json(os.path.join(proc, f"{tag}_{split}_sensitivity_siblings_info.json"), info, exclusive)
        _metrics(sp, sc, f"{tag}_sensitivity_siblings_removed", split, pairs, proc, exclusions_path, exclusive)
    _write_json(os.path.join(proc, f"{tag}_{split}_provenance.json"), {
        "split": split, "tag": tag, "systems": list(systems), "pairs": [list(p) for p in pairs or []],
        "n_product_items": len(p_items), "n_country_items": len(c_items), "sensitivity_outputs": bool(sens),
        "run_id": run.run_id if ts is not None else None,
        "exclusions_sha256": ts.sha256 if ts is not None else None,
        "benchmark_sha256": {f: run_control.sha256_file(os.path.join(run.paths.gen if ts is not None else (gen_dir or GEN), f))
                             for f in ("product_benchmark.csv", "country_benchmark.csv")}}, exclusive)
    return prows, crows, mrows
