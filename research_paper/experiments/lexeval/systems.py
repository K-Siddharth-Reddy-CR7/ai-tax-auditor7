"""Uniform adapters for B, S0, S1 and single-change variants.

Every adapter returns a StdOut dict:
  status          OK | ABSTAINED | INVALID | ERROR
  prod_hs         6-digit HS code shown to the user, or None (no product answer)
  prod_fabricated True if the code is S0's hard-coded fallback "8471.30"
  category        product category used downstream (or None)
  country_iso     ISO alpha-2 the system *identified* (None = not identified)
  default_rates   True if default duty/VAT were applied for an unknown jurisdiction
  duty_rate, gst_rate, currency, landing_cost, local_landing_cost
  fx_substituted  True if a missing exchange rate was silently replaced by 1.0
  policy_id       top retrieved policy id (or None)
  flags           explicit, user-visible warnings/reasons
Original functions are called unmodified. Variants re-compose ORIGINAL stage
functions and change exactly one component per ladder step (see LADDER).
"""
from lexitax_v2 import S1Config, run_s1
from lexitax_v2.jurisdiction import resolve_jurisdiction
from lexitax_v2.legacy import server
from lexitax_v2.product import resolve_product
from lexitax_v2.reference import ISO_TO_TABLE, TABLE_TO_ISO, tax_rows_by_iso
from lexitax_v2.validation import validate_payload

SRV = server()
S0_FALLBACK_HS = "8471.30"


def _std(**kw):
    base = dict(status="OK", prod_hs=None, prod_fabricated=False, category=None, country_iso=None,
                default_rates=False, duty_rate=None, gst_rate=None, currency=None,
                landing_cost=None, local_landing_cost=None, fx_substituted=False,
                policy_id=None, flags=[])
    base.update(kw)
    return base


# ----------------------------------------------------------------------------- B
def run_B(product, dest, price, qty, ship):
    try:
        r = SRV.run_normal_auditor_pipeline(product, dest, price, qty, ship)
    except Exception as e:  # noqa: BLE001 - any crash is an explicit failure
        return _std(status="ERROR", flags=[f"exception: {e}"])
    if "error" in r:
        return _std(status="ERROR", flags=[r["error"]])
    hs = str(r["hs_code"])
    iso = TABLE_TO_ISO.get(r["destination"])
    flags = ["HS code N/A"] if hs == "N/A" else []
    return _std(prod_hs=None if hs == "N/A" else hs, category=None if hs == "N/A" else _cat_of(hs, r["product"]),
                country_iso=iso, default_rates=iso is None,
                duty_rate=float(r["import_duty_rate"]), gst_rate=float(r["gst_vat_rate"]),
                landing_cost=r["landing_cost"], flags=flags)


def _cat_of(hs, product_name):
    for p in SRV.PRODUCTS:
        if p["Product"] == product_name:
            return p["Category"]
    return None


# ----------------------------------------------------------------------------- S0
def _from_s0_data(d):
    hs = str(d["hs_code"])
    fabricated = hs == S0_FALLBACK_HS
    iso = TABLE_TO_ISO.get(d["matched_country"])
    rp = d.get("retrieved_policies") or []
    return _std(prod_hs=hs.replace(".", ""), prod_fabricated=fabricated, category=d["category"],
                country_iso=iso, default_rates=iso is None, duty_rate=d["duty_rate"],
                gst_rate=d["gst_rate"], currency=d["currency"], landing_cost=d["landing_cost"],
                local_landing_cost=d["local_landing_cost"],
                fx_substituted=d["currency"] not in SRV.EXCHANGE_RATES,
                policy_id=rp[0].get("Policy_ID") if rp else None)


def run_S0(product, dest, price, qty, ship):
    try:
        d = SRV.run_agentic_auditor_pipeline(product, dest, price, qty, ship)
    except Exception as e:  # noqa: BLE001
        return _std(status="ERROR", flags=[f"exception: {e}"])
    return _from_s0_data(d)


# ----------------------------------------------------------------------------- S1
def run_S1(product, dest, price, qty, ship, config=S1Config()):
    r = run_s1({"product_name": product, "destination": dest, "price": price,
                "quantity": qty, "shipping": ship}, config)
    if r["status"] == "INVALID_INPUT":
        return _std(status="INVALID", flags=r["reasons"])
    p, j = r["product"], r["jurisdiction"]
    costs, fx, tax = r["costs"] or {}, r["fx"] or {}, r["tax"] or {}
    return _std(status="OK" if r["status"] == "RESOLVED" else "ABSTAINED",
                prod_hs=p["hs_code"] if p["status"] == "RESOLVED" else None,
                category=p["category"] if p["status"] == "RESOLVED" else None,
                country_iso=j["iso2"], duty_rate=tax.get("duty_rate"), gst_rate=tax.get("gst_rate"),
                currency=tax.get("currency"), landing_cost=costs.get("landing_cost"),
                local_landing_cost=fx.get("local_landing_cost"),
                policy_id=(r["policy"] or {}).get("policy_ids", [None])[0], flags=list(r["reasons"]))


# ----------------------------------------------------------------------------- mirrors of S0 stages
def _s0_product_mirror(name, use_overlap=True):
    """Line-by-line mirror of server.product_agent with an optional tier-3 switch."""
    tokenize = SRV.tokenize
    query = name.lower()
    matched = None
    for p in SRV.PRODUCTS:
        pn = p.get("Product", "").lower()
        if pn == query or pn.startswith(query):
            matched = p
            break
    if not matched:
        for p in SRV.PRODUCTS:
            if query in p.get("Product", "").lower():
                matched = p
                break
    if not matched and use_overlap:
        q = set(tokenize(query))
        best = 0
        for p in SRV.PRODUCTS:
            ov = len(q & set(tokenize(p.get("Product", ""))))
            if ov > best:
                best, matched = ov, p
    if not matched:
        matched = {"Product": name.title(), "HS_Code": S0_FALLBACK_HS, "Category": "Electronics", "Unit": "Piece"}
    return matched


def _s0_tax_mirror(dest, use_partial=True):
    """Mirror of server.tax_agent with an optional partial-match switch."""
    d = dest.lower()
    for t in SRV.TAXES:
        if t.get("Country", "").lower() == d:
            return t
    if use_partial:
        for t in SRV.TAXES:
            c = t.get("Country", "").lower()
            if d in c or c in d:
                return t
    return {"Country": dest.title(), "Currency": "USD", "Default_Import_Duty_Percent": 5.0, "GST_VAT_Percent": 10.0}


DEFAULT_ROW = {"Currency": "USD", "Default_Import_Duty_Percent": 5.0, "GST_VAT_Percent": 10.0}


def run_composite(product, dest, price, qty, ship, *, validate=False, product_mode="s0",
                  country_mode="s0", config=S1Config()):
    """Re-compose the pipeline from original stage functions; one switch per component.

    product_mode: s0 | s0_no_overlap | s0_abstain | s1
    country_mode: s0 | s0_exact_only | iso_default | iso_refuse
    """
    flags = []
    # 1. input stage
    if validate:
        clean, errs = validate_payload({"product_name": product, "destination": dest,
                                        "price": price, "quantity": qty, "shipping": ship})
        if errs:
            return _std(status="INVALID", flags=errs)
        data = {"product_name": clean["product_name"], "destination": clean["destination"],
                "price": clean["price"], "quantity": clean["quantity"], "shipping": clean["shipping"]}
    else:
        try:
            data = SRV.input_agent(product, dest, price, qty, ship)
        except Exception as e:  # noqa: BLE001
            return _std(status="ERROR", flags=[f"exception: {e}"])

    # 2. product stage
    prod_ok, fabricated = True, False
    if product_mode in ("s0", "s0_no_overlap", "s0_abstain"):
        m = _s0_product_mirror(data["product_name"], use_overlap=product_mode != "s0_no_overlap")
        hs, cat = str(m.get("HS_Code")), m.get("Category")
        fabricated = hs == S0_FALLBACK_HS and "Product_ID" not in m
        if product_mode == "s0_abstain" and fabricated:
            prod_ok, hs, cat, fabricated = False, None, None, False
            flags.append("product not resolved")
    elif product_mode == "s1":
        pr = resolve_product(data["product_name"], config.product_min_coverage,
                             config.product_typo_max_edits, config.product_typo_min_len)
        prod_ok = pr["status"] == "RESOLVED"
        hs, cat = pr["hs_code"], pr["category"]
        if not prod_ok:
            flags.append(f"product not resolved ({pr['reason']})")
    else:
        raise ValueError(product_mode)

    # 3. jurisdiction / tax stage
    refuse = False
    iso = None
    if country_mode in ("s0", "s0_exact_only"):
        row = _s0_tax_mirror(data["destination"], use_partial=country_mode == "s0")
        iso = TABLE_TO_ISO.get(row["Country"])
        policy_country = data["destination"]          # S0 queries policies with the raw input
    else:
        j = resolve_jurisdiction(data["destination"], config.country_typo_max_edits, config.country_typo_min_len)
        iso = j["iso2"]
        if j["status"] == "SUPPORTED":
            row = tax_rows_by_iso()[iso]
            policy_country = row["Country"]
        elif country_mode == "iso_default":
            row = dict(DEFAULT_ROW, Country=data["destination"].title())
            policy_country = data["destination"]
        else:
            row, refuse, policy_country = None, True, None
            flags.append(f"destination {j['status'].lower()}")
    default_rates = row is not None and TABLE_TO_ISO.get(row["Country"]) is None

    # 4. calculation (original arithmetic)
    gate_on_product = product_mode in ("s0_abstain", "s1")
    out = _std(prod_hs=hs.replace(".", "") if prod_ok and hs else None, prod_fabricated=fabricated,
               category=cat if prod_ok else None, country_iso=iso, default_rates=default_rates)
    if row is not None:
        out.update(duty_rate=float(row["Default_Import_Duty_Percent"]), gst_rate=float(row["GST_VAT_Percent"]),
                   currency=row.get("Currency", "USD"))
    if row is not None and (prod_ok or not gate_on_product):
        d = SRV.calculation_agent({"price": data["price"], "quantity": data["quantity"],
                                   "shipping": data["shipping"], "duty_rate": out["duty_rate"],
                                   "gst_rate": out["gst_rate"], "currency": out["currency"]})
        out["landing_cost"] = d["landing_cost"]
        fx_known = out["currency"] in SRV.EXCHANGE_RATES
        if country_mode == "iso_refuse":
            out["local_landing_cost"] = d["local_landing_cost"] if fx_known else None
            if not fx_known:
                flags.append("exchange rate unavailable")
        else:
            out["local_landing_cost"] = d["local_landing_cost"]
            out["fx_substituted"] = not fx_known
    # 5. policy lookup (original retriever)
    if prod_ok and policy_country is not None and cat is not None:
        pd_ = SRV.rag_policy_agent({"destination": policy_country, "category": cat})
        rp = pd_.get("retrieved_policies") or []
        out["policy_id"] = rp[0].get("Policy_ID") if rp else None
    if refuse or not prod_ok:
        out["status"] = "ABSTAINED"
    out["flags"] = flags
    return out


# ----------------------------------------------------------------------------- registry
LADDER = [  # each step changes exactly one component relative to the previous one
    ("L0_S0", dict(validate=False, product_mode="s0", country_mode="s0")),
    ("L1_+validation", dict(validate=True, product_mode="s0", country_mode="s0")),
    ("L2_+iso_identification", dict(validate=True, product_mode="s0", country_mode="iso_default")),
    ("L3_+tax_availability_refusal", dict(validate=True, product_mode="s0", country_mode="iso_refuse")),
    ("L4_+product_abstention", dict(validate=True, product_mode="s0_abstain", country_mode="iso_refuse")),
    ("L5_+s1_product_tiers(=S1)", dict(validate=True, product_mode="s1", country_mode="iso_refuse")),
]

EXTRA_ABLATIONS = [
    ("S0_-token_overlap", dict(validate=False, product_mode="s0_no_overlap", country_mode="s0")),
    ("S0_-partial_country", dict(validate=False, product_mode="s0", country_mode="s0_exact_only")),
]


def primary_systems(s1_config=S1Config()):
    return {"B": run_B, "S0": run_S0,
            "S1": lambda *a: run_S1(*a, config=s1_config)}


def ladder_systems(s1_config=S1Config()):
    systems = {}
    for name, kw in LADDER + EXTRA_ABLATIONS:
        systems[name] = (lambda kw: (lambda *a: run_composite(*a, config=s1_config, **kw)))(kw)
    for name, cfg in (("S1_-coverage_guard", dict(product_min_coverage=0.0)),
                      ("S1_-typo_tier", dict(product_typo_max_edits=0)),
                      ("S1_+country_typo", dict(country_typo_max_edits=1))):
        c = S1Config(**{**s1_config.__dict__, **cfg})
        systems[name] = (lambda c: (lambda *a: run_S1(*a, config=c)))(c)
    return systems


