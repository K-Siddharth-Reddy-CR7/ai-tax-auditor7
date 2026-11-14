"""Jurisdiction resolution against ISO 3166-1 (pycountry / Debian iso-codes).

Identification (which country is meant?) is kept separate from tax-data
availability (does the application have rates for it?).
"""
from functools import lru_cache

import pycountry

from .normalize import normalize_text, osa_distance
from .reference import TABLE_TO_ISO, tax_rows_by_iso

ALIAS_FIELDS = ("alpha_2", "alpha_3", "name", "official_name", "common_name")


@lru_cache(maxsize=1)
def alias_index():
    """normalised alias -> set of ISO alpha-2 codes (sources: ISO 3166-1 fields + table names)."""
    idx = {}
    for c in pycountry.countries:
        for f in ALIAS_FIELDS:
            v = getattr(c, f, None)
            if v:
                idx.setdefault(normalize_text(v), set()).add(c.alpha_2)
    for name, iso in TABLE_TO_ISO.items():
        idx.setdefault(normalize_text(name), set()).add(iso)
    return idx


def resolve_jurisdiction(text, typo_max_edits: int = 0, typo_min_len: int = 5) -> dict:
    norm = normalize_text(text)
    out = {"input": text, "normalised": norm, "status": None, "iso2": None,
           "iso_name": None, "method": None, "tax_data_available": False,
           "table_country": None, "candidates": []}
    if not norm:
        out.update(status="UNRESOLVED", method="empty")
        return out
    idx = alias_index()
    cands = idx.get(norm, set())
    method = "exact_alias" if cands else None
    if not cands and typo_max_edits > 0 and len(norm) >= typo_min_len:
        near = set()
        for alias, isos in idx.items():
            if len(alias) >= typo_min_len and osa_distance(norm, alias, typo_max_edits) <= typo_max_edits:
                near |= isos
        cands, method = near, "typo_alias"
    out["candidates"] = sorted(cands)
    if len(cands) != 1:
        out.update(status="AMBIGUOUS" if len(cands) > 1 else "UNRESOLVED", method=method or "no_match")
        return out
    iso = next(iter(cands))
    country = pycountry.countries.get(alpha_2=iso)
    row = tax_rows_by_iso().get(iso)
    out.update(iso2=iso, iso_name=country.name if country else None, method=method,
               tax_data_available=row is not None,
               table_country=row["Country"] if row else None,
               status="SUPPORTED" if row else "UNSUPPORTED_JURISDICTION")
    return out
