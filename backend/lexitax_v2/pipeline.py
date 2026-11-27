"""S1: corrected staged pre-assessment pipeline.

Stage order: validate -> resolve jurisdiction -> check tax-data availability ->
resolve product -> (if both resolved) original landed-cost arithmetic ->
original TF-IDF policy lookup -> report. Every stage records its outcome and
latency; the pipeline never substitutes default rates, codes or exchange rates.
"""
import copy
import time

from .config import S1Config
from .jurisdiction import resolve_jurisdiction
from .legacy import server
from .product import resolve_product
from .reference import tax_rows_by_iso
from .validation import validate_payload


def _stage(trace, name, t0, status, detail=""):
    trace.append({"stage": name, "status": status, "detail": detail,
                  "latency_ms": round((time.perf_counter() - t0) * 1000, 4)})


def run_s1(payload: dict, config: S1Config = S1Config()) -> dict:
    srv = server()
    trace = []
    result = {"system": "S1", "status": None, "reasons": [], "input": dict(payload),
              "product": None, "jurisdiction": None, "tax": None, "costs": None,
              "fx": None, "policy": None, "trace": trace}

    t0 = time.perf_counter()
    clean, errors = validate_payload(payload)
    _stage(trace, "validation", t0, "INVALID" if errors else "OK", "; ".join(errors))
    if errors:
        result.update(status="INVALID_INPUT", reasons=errors)
        return result

    t0 = time.perf_counter()
    jur = resolve_jurisdiction(clean["destination"], config.country_typo_max_edits,
                               config.country_typo_min_len)
    result["jurisdiction"] = jur
    _stage(trace, "jurisdiction", t0, jur["status"], jur.get("iso2") or "")

    t0 = time.perf_counter()
    prod = resolve_product(clean["product_name"], config.product_min_coverage,
                           config.product_typo_max_edits, config.product_typo_min_len)
    result["product"] = prod
    _stage(trace, "product", t0, prod["status"], prod.get("hs_code") or prod.get("reason") or "")

    reasons = []
    if jur["status"] == "UNSUPPORTED_JURISDICTION":
        reasons.append(f"jurisdiction identified as {jur['iso2']} but no tax data is available")
    elif jur["status"] != "SUPPORTED":
        reasons.append(f"destination not resolved ({jur['status'].lower()})")
    if prod["status"] != "RESOLVED":
        reasons.append(f"product not resolved ({prod['reason']})")

    t0 = time.perf_counter()
    if jur["status"] == "SUPPORTED":
        row = tax_rows_by_iso()[jur["iso2"]]
        result["tax"] = {"country": row["Country"], "currency": row.get("Currency"),
                         "duty_rate": float(row["Default_Import_Duty_Percent"]),
                         "gst_rate": float(row["GST_VAT_Percent"])}
    _stage(trace, "tax_lookup", t0, "OK" if result["tax"] else "SKIPPED")

    can_compute = result["tax"] is not None and (
        prod["status"] == "RESOLVED" or not config.require_product_for_costs)
    t0 = time.perf_counter()
    if can_compute:
        data = {"price": clean["price"], "quantity": clean["quantity"],
                "shipping": clean["shipping"], "duty_rate": result["tax"]["duty_rate"],
                "gst_rate": result["tax"]["gst_rate"], "currency": result["tax"]["currency"]}
        data = srv.calculation_agent(data)  # original arithmetic, unchanged
        fx_known = result["tax"]["currency"] in srv.EXCHANGE_RATES
        result["costs"] = {k: data[k] for k in (
            "product_cost", "customs_value", "customs_duty", "taxable_value", "gst_vat",
            "landing_cost", "effective_tax_rate", "tax_burden_per_unit", "landed_cost_per_unit")}
        result["fx"] = {"currency": result["tax"]["currency"],
                        "rate": data["exchange_rate"] if fx_known else None,
                        "local_landing_cost": data["local_landing_cost"] if fx_known else None,
                        "available": fx_known}
        if not fx_known:
            reasons.append(f"no exchange rate for {result['tax']['currency']}; local amount not computed")
    _stage(trace, "calculation", t0, "OK" if can_compute else "SKIPPED")

    t0 = time.perf_counter()
    if result["tax"] is not None and prod["status"] == "RESOLVED":
        pdata = srv.rag_policy_agent({"destination": result["tax"]["country"],
                                      "category": prod["category"]})  # original retriever
        result["policy"] = {k: pdata.get(k) for k in (
            "policy", "compliance", "source_type", "risk_level", "risk_verdict")}
        result["policy"]["policy_ids"] = [p.get("Policy_ID") for p in pdata.get("retrieved_policies", [])]
    _stage(trace, "policy_lookup", t0, "OK" if result["policy"] else "SKIPPED")

    result["reasons"] = reasons
    if prod["status"] == "RESOLVED" and jur["status"] == "SUPPORTED":
        result["status"] = "RESOLVED"
    else:
        result["status"] = "ABSTAINED"
    return copy.deepcopy(result)
