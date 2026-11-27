import math

import pycountry
import pytest

from lexitax_v2 import S1Config, run_s1
from lexitax_v2.jurisdiction import alias_index, resolve_jurisdiction
from lexitax_v2.legacy import server
from lexitax_v2.normalize import canonical, normalize_text, osa_distance, singular
from lexitax_v2.product import resolve_product
from lexitax_v2.reference import TABLE_TO_ISO, catalogue, tax_rows_by_iso
from lexitax_v2.validation import validate_payload

SRV = server()


def payload(product="Laptop", dest="India", price=800, qty=2, ship=100):
    return {"product_name": product, "destination": dest, "price": price,
            "quantity": qty, "shipping": ship}


# ---------- normalisation ----------
def test_normalize_and_plural():
    assert normalize_text("  Türkiye ") == "turkiye"
    assert normalize_text("Côte d'Ivoire") == "cote d ivoire"
    assert singular("batteries") == "battery" and singular("glasses") == "glass"
    assert singular("apparatus") == "apparatus" and singular("headphones") == "headphone"
    assert canonical("Wireless  HEADPHONES") == canonical("wireless headphone")


def test_osa_distance():
    assert osa_distance("laptop", "laptpo") == 1  # transposition
    assert osa_distance("laptop", "lapto") == 1
    assert osa_distance("laptop", "desktop") == 4  # l->d, a->e, p->s, +k
    assert osa_distance("abc", "abc") == 0


# ---------- reference data ----------
def test_catalogue_structure():
    by_name, bases = catalogue()
    assert len(by_name) == 1200 and len(bases) == 60
    assert len({b["hs"] for b in bases.values()}) == 43


def test_table_iso_mapping_matches_iso3166():
    assert len(TABLE_TO_ISO) == 40 == len(tax_rows_by_iso())
    for name, iso in TABLE_TO_ISO.items():
        if name == "Turkey":  # renamed "Türkiye" in ISO 3166-1 (2022)
            assert pycountry.countries.get(alpha_2="TR").name == "Türkiye"
            continue
        assert pycountry.countries.lookup(name).alpha_2 == iso, name


def test_alias_index_has_no_collisions():
    collisions = {a: s for a, s in alias_index().items() if len(s) > 1}
    assert collisions == {}


# ---------- jurisdiction: identification separate from tax-data availability ----------
@pytest.mark.parametrize("text,status,iso", [
    ("India", "SUPPORTED", "IN"), ("india ", "SUPPORTED", "IN"), ("US", "SUPPORTED", "US"),
    ("USA", "SUPPORTED", "US"), ("United States of America", "SUPPORTED", "US"),
    ("GBR", "SUPPORTED", "GB"), ("Türkiye", "SUPPORTED", "TR"), ("Turkey", "SUPPORTED", "TR"),
    ("Viet Nam", "SUPPORTED", "VN"), ("Niger", "UNSUPPORTED_JURISDICTION", "NE"),
    ("Peru", "UNSUPPORTED_JURISDICTION", "PE"), ("Korea", "UNRESOLVED", None),
    ("UK", "UNRESOLVED", None), ("Atlantis", "UNRESOLVED", None), ("", "UNRESOLVED", None),
])
def test_resolve_jurisdiction(text, status, iso):
    r = resolve_jurisdiction(text)
    assert (r["status"], r["iso2"]) == (status, iso)
    assert r["tax_data_available"] == (status == "SUPPORTED")


def test_country_typo_tolerance_is_off_by_default_and_optional():
    assert resolve_jurisdiction("Indai")["status"] == "UNRESOLVED"
    assert resolve_jurisdiction("Germnay", typo_max_edits=1)["iso2"] == "DE"


# ---------- product resolution ----------
@pytest.mark.parametrize("text,status,hs,tier_prefix", [
    ("Laptop", "RESOLVED", "847130", "T1"),
    ("Laptop Model X", "RESOLVED", "847130", "T1"),
    ("LAPTOPS", "RESOLVED", "847130", "T1"),
    ("Laptpo", "RESOLVED", "847130", "T3"),
    ("Microwave oven 25L", "RESOLVED", "851650", "T2"),
    ("router modem", "RESOLVED", "851762", "T2"),
    ("Car", "ABSTAINED", None, None),
    ("Cotton T-Shirt", "ABSTAINED", None, None),
    ("laptop sleeve neoprene", "ABSTAINED", None, "T2"),
])
def test_resolve_product(text, status, hs, tier_prefix):
    r = resolve_product(text)
    assert r["status"] == status and r["hs_code"] == hs
    if tier_prefix:
        assert r["tier"].startswith(tier_prefix)


def test_product_ambiguity_abstains():
    # "Memory Card" (852351) and "Graphics Card" (847180) both contained -> different HS -> abstain
    r = resolve_product("memory card graphics card")
    assert r["status"] == "ABSTAINED" and r["reason"] == "ambiguous_multiple_hs"


def test_no_fabricated_hs_code():
    r = resolve_product("frozen shrimp")
    assert r["status"] == "ABSTAINED" and r["hs_code"] is None


# ---------- validation ----------
@pytest.mark.parametrize("bad", [
    payload(product="   "), payload(dest=""), payload(price=-1), payload(price=0),
    payload(price=float("nan")), payload(qty=0), payload(qty=2.5), payload(qty="2.7"),
    payload(ship=-5), payload(price="abc"), {"product_name": "Laptop", "destination": "India"},
])
def test_invalid_inputs_rejected(bad):
    r = run_s1(bad)
    assert r["status"] == "INVALID_INPUT" and r["reasons"]
    assert r["costs"] is None


def test_valid_numeric_strings_and_integral_floats_accepted():
    clean, errs = validate_payload(payload(price="800", qty=2.0, ship="0"))
    assert errs == [] and clean["quantity"] == 2 and clean["price"] == 800.0


# ---------- pipeline behaviour ----------
def test_unsupported_jurisdiction_refuses_without_defaults():
    r = run_s1(payload(dest="Niger"))
    assert r["status"] == "ABSTAINED"
    assert r["jurisdiction"]["iso2"] == "NE" and r["tax"] is None and r["costs"] is None


def test_unresolved_product_blocks_costs_but_keeps_jurisdiction():
    r = run_s1(payload(product="frozen shrimp"))
    assert r["status"] == "ABSTAINED" and r["costs"] is None
    assert r["jurisdiction"]["status"] == "SUPPORTED" and r["tax"]["duty_rate"] == 10.0


def test_missing_exchange_rate_is_not_replaced_by_one():
    r = run_s1(payload(dest="Denmark"))
    assert r["status"] == "RESOLVED"
    assert r["fx"]["available"] is False and r["fx"]["rate"] is None
    assert r["fx"]["local_landing_cost"] is None


def test_arithmetic_identical_to_original_calculation_agent():
    r = run_s1(payload())
    d = SRV.calculation_agent({"price": 800.0, "quantity": 2, "shipping": 100.0,
                               "duty_rate": 10.0, "gst_rate": 18.0, "currency": "INR"})
    assert r["costs"]["landing_cost"] == d["landing_cost"] == 2206.6


def test_deterministic():
    a, b = run_s1(payload()), run_s1(payload())
    for x in (a, b):
        for s in x["trace"]:
            s.pop("latency_ms")
    assert a == b


# ---------- integration: canonical synthetic transactions ----------
def test_s1_matches_s0_on_canonical_catalogue_transactions():
    """On the 400 shipped (canonical) transactions S1 must reproduce S0's financial outputs."""
    for t in SRV.SAMPLE_TRANSACTIONS:
        s0 = SRV.run_agentic_auditor_pipeline(t["Product"], t["Destination_Country"],
                                              t["Unit_Price_USD"], t["Quantity"],
                                              t["Shipping_USD"], t["Origin_Country"])
        s1 = run_s1({"product_name": t["Product"], "destination": t["Destination_Country"],
                     "price": t["Unit_Price_USD"], "quantity": t["Quantity"],
                     "shipping": t["Shipping_USD"], "source_country": t["Origin_Country"]})
        assert s1["status"] == "RESOLVED"
        assert s1["product"]["hs_code"] == str(s0["hs_code"]) == str(t["HS_Code"])
        assert math.isclose(s1["costs"]["landing_cost"], s0["landing_cost"])
        assert s1["policy"]["policy_ids"][0] == s0["retrieved_policies"][0]["Policy_ID"]


def test_original_s0_behaviour_preserved():
    """Regression guard: the original pipeline is used as-is (including its known defects)."""
    s0 = SRV.run_agentic_auditor_pipeline("Mobile Phone", "US", 100, 1, 10)
    assert s0["matched_country"] == "Australia"
    s0 = SRV.run_agentic_auditor_pipeline("Cotton T-Shirt", "India", 100, 1, 10)
    assert s0["hs_code"] == "8471.30"


def test_config_is_frozen():
    with pytest.raises(Exception):
        S1Config().product_min_coverage = 0.1
