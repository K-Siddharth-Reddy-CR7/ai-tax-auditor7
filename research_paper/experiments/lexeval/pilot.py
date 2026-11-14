"""10-item human verification pilot: stratified, seeded selection from the DEV split.

Reviewers see the input, the expected outcome, the reference source and the rule that
produced the label. They never see any system output.
"""
import csv
import os

from lexitax_v2.reference import ISO_TO_TABLE

from .build_common import read_csv
from .perturb import rng_for
from .paths import GEN, PILOT
from .refdata import load_hs6

STRATA = [  # (benchmark, subset, filter, description)
    ("product", "PA", lambda r: r["transform"] == "typo", "catalogue name with a one-edit typo"),
    ("product", "PA", lambda r: r["transform"] in ("plural", "reorder"), "catalogue name, plural/reordered"),
    ("product", "PB", lambda r: r["transform"] == "none", "HS 2022 text of a catalogue code"),
    ("product", "PC", lambda r: True, "HS 2022 text of an unsupported subheading in a catalogue chapter"),
    ("product", "PD", lambda r: True, "HS 2022 text from an unrelated chapter"),
    ("product", "PE", lambda r: True, "rule-generated ambiguous product token"),
    ("country", "CD", lambda r: True, "CLDR localised country name (held-out alias)"),
    ("country", "CB", lambda r: r["tax_data_available"] == "False", "ISO name of a country without tax data"),
    ("country", "CC", lambda r: True, "one-edit typo of a country name"),
    ("country", "CE", lambda r: True, "rule-generated ambiguous country token"),
]

FIELDS = ["pilot_id", "task", "input_text", "expected_outcome", "reference_source", "reference_detail",
          "label_rule", "reviewer", "agree(Y/N/unsure)", "corrected_outcome", "comment", "minutes_spent"]


def _expected_product(r, hs6):
    if r["expected"] == "ANSWER":
        return (f"ANSWER HS {r['label_hs']}",
                f"HS 2022 {r['label_hs']}: {hs6.get(r['label_hs'], '(catalogue code)')}")
    return (f"ABSTAIN ({r['abstain_reason']})",
            f"HS 2022 {r['parent']}: {hs6.get(r['parent'], '')}" if r["subset"] in ("PC", "PD") else r["label_source"])


def _expected_country(r):
    iso = r["expected_iso"]
    if iso:
        beh = "compute with its tax rates" if r["tax_data_available"] == "True" else "refuse: no tax data"
        return (f"IDENTIFY {iso}; {beh}", f"ISO 3166-1 {iso}" + (f" (table: {ISO_TO_TABLE[iso]})" if iso in ISO_TO_TABLE else ""))
    return ("DO NOT IDENTIFY (ambiguous / not a country); refuse", r["label_source"])


def build_pilot(seed):
    hs6, _ = load_hs6()
    prod = [r for r in read_csv(os.path.join(GEN, "product_benchmark.csv")) if r["split"] == "dev"]
    ctry = [r for r in read_csv(os.path.join(GEN, "country_benchmark.csv")) if r["split"] == "dev"]
    rows = []
    for i, (bench, subset, filt, desc) in enumerate(STRATA, start=1):
        pool = sorted([r for r in (prod if bench == "product" else ctry) if r["subset"] == subset and filt(r)],
                      key=lambda r: r["item_id"])
        if not pool:
            continue
        r = rng_for(seed, "pilot", i).choice(pool)
        exp, detail = _expected_product(r, hs6) if bench == "product" else _expected_country(r)
        rows.append({"pilot_id": f"P{i:02d}", "task": f"{bench}: {desc}", "input_text": r["text"],
                     "expected_outcome": exp, "reference_source": r["label_source"], "reference_detail": detail,
                     "label_rule": f"subset {r['subset']}, transform={r['transform']}, item {r['item_id']}"})
    os.makedirs(PILOT, exist_ok=True)
    with open(os.path.join(PILOT, "pilot_review_sheet.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            for reviewer in ("R1", "R2"):
                w.writerow({**r, "reviewer": reviewer})
    return rows
