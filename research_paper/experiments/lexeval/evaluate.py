"""Run systems on the frozen benchmarks and score them (raw -> processed results)."""
import csv
import json
import os
from collections import defaultdict

from lexitax_v2.reference import ISO_TO_TABLE, catalogue, tax_rows_by_iso

from . import build_malformed, scoring
from .build_common import read_csv
from .paths import GEN, RESULTS
from .stats import holm, mcnemar_exact, wilson
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


def load(split):
    p = [r for r in read_csv(os.path.join(GEN, "product_benchmark.csv")) if r["split"] == split]
    c = [r for r in read_csv(os.path.join(GEN, "country_benchmark.csv")) if r["split"] == split]
    m = build_malformed.build()  # in-memory: preserves Python types (str vs float) of malformed values
    return p, c, m


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


def run_product_task(items, systems, raw_fh=None):
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
            row = dict(task="product", item_id=it["item_id"], subset=it["subset"], system=name,
                       outcome=outcome, fabricated=out["prod_fabricated"], prod_hs=out["prod_hs"],
                       label_hs=it["label_hs"], expected=it["expected"], propagation=prop,
                       flagged=flagged, rel_cost_error=rel, policy_wrong=policy_wrong)
            rows.append(row)
            if raw_fh:
                raw_fh.write(json.dumps({"row": row, "output": out}, default=str) + "\n")
    return rows


def run_country_task(items, systems, raw_fh=None):
    _, bases = catalogue()
    base_names = sorted(bases)
    rows = []
    for i, it in enumerate(items):
        bname = base_names[i % len(base_names)]
        price, qty, ship = _numerics(i)
        iso = it["expected_iso"] or None
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
            row = dict(task="country", item_id=it["item_id"], subset=it["subset"], system=name,
                       identification=ident, tax_behaviour=beh, tax_subtype=sub,
                       country_iso=out["country_iso"], expected_iso=it["expected_iso"],
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


def summarise_by(rows, key_outcome, group_keys=("system", "subset")):
    groups = defaultdict(list)
    for r in rows:
        groups[tuple(r[k] for k in group_keys)].append(r[key_outcome])
        groups[tuple(r[k] if k == "system" else "ALL" for k in group_keys)].append(r[key_outcome])
    out = []
    for g, outcomes in sorted(groups.items()):
        s = scoring.summarise(outcomes)
        for metric, k in (("coverage", "answered"), ("decision_accuracy", None), ("silent_error_rate", scoring.SILENT)):
            num = s["answered"] if metric == "coverage" else (
                s[scoring.CORRECT] + s[scoring.SAFE] if metric == "decision_accuracy" else s[scoring.SILENT])
            lo, hi = wilson(num, s["n"])
            s[f"{metric}_ci_low"], s[f"{metric}_ci_high"] = lo, hi
        out.append(dict(zip(group_keys, g), **s))
    return out


def paired_tests(rows, key_outcome, pairs, task):
    by_sys = defaultdict(dict)
    for r in rows:
        by_sys[r["system"]][r["item_id"]] = r[key_outcome]
    tests = []
    for a, b in pairs:
        ids = sorted(set(by_sys[a]) & set(by_sys[b]))
        for indicator, pred in (("decision_correct", lambda o: o in (scoring.CORRECT, scoring.SAFE)),
                                ("silent_error", lambda o: o == scoring.SILENT)):
            xa = [pred(by_sys[a][i]) for i in ids]
            xb = [pred(by_sys[b][i]) for i in ids]
            n01, n10, p = mcnemar_exact(xa, xb)
            tests.append(dict(task=task, metric=indicator, system_a=a, system_b=b, n=len(ids),
                              rate_a=sum(xa) / len(ids), rate_b=sum(xb) / len(ids),
                              diff_b_minus_a=(sum(xb) - sum(xa)) / len(ids),
                              a_false_b_true=n01, a_true_b_false=n10, p_value=p))
    return tests


def write_rows(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not rows:
        return
    fields = list(rows[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def evaluate(systems, split="test", tag="primary", pairs=(("B", "S0"), ("S0", "S1"), ("B", "S1"))):
    p_items, c_items, m_items = load(split)
    raw_dir = os.path.join(RESULTS, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    with open(os.path.join(raw_dir, f"{tag}_{split}_outputs.jsonl"), "w", encoding="utf-8") as fh:
        prows = run_product_task(p_items, systems, fh)
        crows = run_country_task(c_items, systems, fh)
    mrows = run_malformed(m_items, systems)
    proc = os.path.join(RESULTS, "processed")
    write_rows(os.path.join(proc, f"{tag}_{split}_product_items.csv"), prows)
    write_rows(os.path.join(proc, f"{tag}_{split}_country_items.csv"), crows)
    write_rows(os.path.join(proc, f"{tag}_{split}_malformed_items.csv"), mrows)
    write_rows(os.path.join(proc, f"{tag}_{split}_product_summary.csv"), summarise_by(prows, "outcome"))
    write_rows(os.path.join(proc, f"{tag}_{split}_identification_summary.csv"), summarise_by(crows, "identification"))
    write_rows(os.path.join(proc, f"{tag}_{split}_tax_behaviour_summary.csv"), summarise_by(crows, "tax_behaviour"))
    if pairs:
        tests = (paired_tests(prows, "outcome", pairs, "product")
                 + paired_tests(crows, "identification", pairs, "identification")
                 + paired_tests(crows, "tax_behaviour", pairs, "tax_behaviour"))
        for t, adj in zip(tests, holm([t["p_value"] for t in tests])):
            t["p_holm"] = adj
        write_rows(os.path.join(proc, f"{tag}_{split}_paired_tests.csv"), tests)
    return prows, crows, mrows
