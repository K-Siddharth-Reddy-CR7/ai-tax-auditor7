"""Reference data: catalogue structure and the tax-table -> ISO 3166-1 mapping."""
import re
from functools import lru_cache

from .legacy import server
from .normalize import canonical, tokens

# Variant suffixes used to generate the 1,200-row synthetic catalogue (60 base types x 20).
VARIANT_SUFFIX = re.compile(
    r" (Standard|Basic|Premium|Pro|Advanced|Lite|Plus|Max|Mini|Ultra|Gen \d|Series [ABC]|Model [XYZ]|2026)$"
)

# The 40 jurisdictions of taxes.json mapped to ISO 3166-1 alpha-2.
# Verified against pycountry (iso-codes) in backend/tests/test_lexitax_v2.py.
# Note: ISO 3166-1 renamed TR to "Türkiye" in 2022; the table still says "Turkey".
TABLE_TO_ISO = {
    "India": "IN", "United States": "US", "Germany": "DE", "United Arab Emirates": "AE",
    "Japan": "JP", "United Kingdom": "GB", "Australia": "AU", "Canada": "CA", "France": "FR",
    "Italy": "IT", "Spain": "ES", "Singapore": "SG", "Malaysia": "MY", "Thailand": "TH",
    "South Korea": "KR", "China": "CN", "Saudi Arabia": "SA", "Brazil": "BR",
    "South Africa": "ZA", "New Zealand": "NZ", "Mexico": "MX", "Indonesia": "ID",
    "Vietnam": "VN", "Philippines": "PH", "Turkey": "TR", "Netherlands": "NL", "Belgium": "BE",
    "Sweden": "SE", "Norway": "NO", "Denmark": "DK", "Switzerland": "CH", "Ireland": "IE",
    "Portugal": "PT", "Poland": "PL", "Austria": "AT", "Argentina": "AR", "Chile": "CL",
    "Egypt": "EG", "Nigeria": "NG", "Greece": "GR",
}
ISO_TO_TABLE = {v: k for k, v in TABLE_TO_ISO.items()}


def base_type(product_name: str) -> str:
    return VARIANT_SUFFIX.sub("", product_name)


@lru_cache(maxsize=1)
def catalogue():
    """Return (products_by_canonical_name, base_types).

    base_types: dict base_name -> {hs, category, unit, tokens(frozenset), canonical,
                                    example_product (first catalogue row of the type)}
    """
    srv = server()
    by_name = {}
    bases = {}
    for p in srv.PRODUCTS:
        name = p["Product"]
        b = base_type(name)
        by_name.setdefault(canonical(name), p)
        if b not in bases:
            bases[b] = {
                "hs": str(p["HS_Code"]),
                "category": p["Category"],
                "unit": p.get("Unit", "Unit"),
                "tokens": frozenset(tokens(b)),
                "canonical": canonical(b),
                "example_product": p,
            }
        elif bases[b]["hs"] != str(p["HS_Code"]):
            raise ValueError(f"Base type {b!r} maps to several HS codes")
    return by_name, bases


@lru_cache(maxsize=1)
def tax_rows_by_iso():
    srv = server()
    rows = {}
    for t in srv.TAXES:
        iso = TABLE_TO_ISO.get(t["Country"])
        if iso is None:
            raise ValueError(f"Tax-table country without ISO mapping: {t['Country']!r}")
        rows[iso] = t
    return rows
