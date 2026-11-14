"""Loading and checking the external reference data (HS 2022, ISO 3166-1, CLDR)."""
import csv
import hashlib
import os
from collections import Counter

from .paths import EXP, config


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_hs6():
    """Return (usable, excluded): dicts code -> description for six-digit HS 2022 rows."""
    cfg = config()
    path = os.path.join(EXP, cfg["hs_file"])
    if sha256(path) != cfg["hs_file_sha256"]:
        raise RuntimeError("HS reference file hash mismatch")
    rows = []
    with open(path, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["level"] == "6":
                rows.append((r["hscode"], r["description"].strip()))
    desc_count = Counter(d for _, d in rows)
    usable, excluded = {}, {}
    for code, desc in rows:
        if not (code.isdigit() and len(code) == 6) or not ("01" <= code[:2] <= "97"):
            excluded[code] = "non-chapter placeholder code"
        elif desc_count[desc] > 1:
            excluded[code] = "description duplicated across codes (unreliable label)"
        else:
            usable[code] = desc
    return usable, excluded


def edition_markers():
    path = os.path.join(EXP, config()["hs_file"])
    codes = set()
    with open(path, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            codes.add(r["hscode"])
    present = {c: c in codes for c in ["8524", "8549", "8806", "851713", "851714"]}
    absent = {c: c not in codes for c in ["851712", "854810"]}
    return {"new_in_2022_present": present, "deleted_in_2022_absent": absent}


def iso_countries():
    import pycountry
    return list(pycountry.countries)


def cldr_names(locales):
    """iso2 -> list of (locale, name) from CLDR via babel."""
    import pycountry
    from babel import Locale
    isos = {c.alpha_2 for c in pycountry.countries}
    out = {}
    for loc in locales:
        terr = Locale(loc).territories
        for code, name in terr.items():
            if code in isos:
                out.setdefault(code, []).append((loc, name))
    return out


def cldr_regions():
    """Non-country CLDR region names in English (UN M.49 numeric regions + supranational codes)."""
    from babel import Locale
    terr = Locale("en").territories
    return {k: v for k, v in terr.items() if k.isdigit() or k in ("EU", "EZ", "UN")}


def versions():
    import importlib.metadata as m
    import babel.core
    return {"pycountry": m.version("pycountry"), "babel": m.version("babel"),
            "cldr": babel.core.get_cldr_version()}
