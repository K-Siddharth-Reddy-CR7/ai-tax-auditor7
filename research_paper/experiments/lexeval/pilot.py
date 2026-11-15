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

STRATA = [  # (benchmark, subset, filter, category label, difficulty)
    ("product", "P2_format", lambda r: r["transform"] == "ws_punct", "formatting variation", "easy"),
    ("product", "P3_typo", lambda r: True, "spelling mistake", "borderline"),
    ("product", "P4_short", lambda r: r["transform"] == "head_noun", "shortened name (answer or decline both acceptable)", "borderline"),
    ("product", "P5_confusable", lambda r: True, "similar but distinct product", "borderline"),
    ("product", "P6_ambiguous", lambda r: True, "ambiguous / underspecified", "ambiguous"),
    ("product", "P7_outside", lambda r: r["look_alike"] == "True", "outside catalogue, look-alike name", "unsupported"),
    ("product", "P8_hs_formal", lambda r: r["transform"] == "other_chapter", "formal HS text, other chapter", "out-of-domain"),
    ("country", "J5_cldr", lambda r: r["tax_data_available"] == "True", "foreign-language country name (supported)", "borderline"),
    ("country", "J3_iso_name", lambda r: r["tax_data_available"] == "False", "real country without tax data", "unsupported"),
    ("country", "J6_ambiguous", lambda r: True, "ambiguous country word", "ambiguous"),
]

FIELDS = ["pilot_id", "task", "input_text", "expected_outcome", "reference_source", "reference_detail",
          "label_rule", "reviewer", "agree(Y/N/unsure)", "corrected_outcome", "comment", "minutes_spent"]


def _expected_product(r, hs6):
    if r["expected"] == "EITHER":
        return (f"ANSWER HS {r['label_hs']} ({r['label_base_types']}) OR DECLINE; a different code is wrong",
                f"catalogue type {r['label_base_types']} (HS {r['label_hs']})")
    if r["expected"] == "ANSWER":
        return (f"ANSWER HS {r['label_hs']}" + (f" ({r['label_base_types']})" if r["label_base_types"] else ""),
                f"HS 2022 {r['label_hs']}: {hs6.get(r['label_hs'], '(catalogue code)')}")
    return (f"ABSTAIN ({r['abstain_reason']})",
            f"HS 2022 {r['parent']}: {hs6.get(r['parent'], '')}" if r["subset"] == "P8_hs_formal" else r["label_source"])


def _expected_country(r):
    iso = r["expected_iso"]
    if iso:
        beh = "compute with its tax rates" if r["tax_data_available"] == "True" else "refuse: no tax data"
        return (f"IDENTIFY {iso}; {beh}", f"ISO 3166-1 {iso}" + (f" (table: {ISO_TO_TABLE[iso]})" if iso in ISO_TO_TABLE else ""))
    return ("DO NOT IDENTIFY (ambiguous / not a country); refuse", r["label_source"])


def build_pilot(seed):
    hs6, _ = load_hs6()
    # Reviewers never see system outputs, so pilot items may come from either split.
    prod = read_csv(os.path.join(GEN, "product_benchmark.csv"))
    ctry = read_csv(os.path.join(GEN, "country_benchmark.csv"))
    rows = []
    for i, (bench, subset, filt, desc, difficulty) in enumerate(STRATA, start=1):
        pool = sorted([r for r in (prod if bench == "product" else ctry) if r["subset"] == subset and filt(r)],
                      key=lambda r: r["item_id"])
        if not pool:
            continue
        r = rng_for(seed, "pilot", i).choice(pool)
        exp, detail = _expected_product(r, hs6) if bench == "product" else _expected_country(r)
        rows.append({"pilot_id": f"P{i:02d}", "task": f"{bench}: {desc} [{difficulty}]", "input_text": r["text"],
                     "expected_outcome": exp, "reference_source": r["label_source"], "reference_detail": detail,
                     "label_rule": f"subset {r['subset']}, transform={r['transform']}, item {r['item_id']}, split {r['split']}"})
    os.makedirs(PILOT, exist_ok=True)
    with open(os.path.join(PILOT, "pilot_review_sheet.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({**r, "reviewer": "R1"})  # one reviewer suffices for a rule sanity check (no IAA claimed)
    return rows


LOOKALIKE_FIELDS = ["item_id", "split", "input_text", "open_products_facts_path", "rule_label",
                    "reviewer_decision(outside / could_be:<catalogue type> / unsure)", "comment"]


def build_lookalike_sheet():
    """P7 look-alikes: names sharing a word with a catalogue type. Whether such a product is outside the
    60 catalogue types can need human judgement (e.g. 'parking cameras' vs 'Video Camera'). Pre-declared
    rule: only items the reviewer marks 'outside' are kept; 'could_be' and 'unsure' items are removed
    before freezing (logged)."""
    rows = [r for r in read_csv(os.path.join(GEN, "product_benchmark.csv"))
            if r["subset"] == "P7_outside" and r["look_alike"] == "True"]
    os.makedirs(PILOT, exist_ok=True)
    path = os.path.join(PILOT, "p7_lookalike_confirmation.csv")
    if os.path.exists(path) and any(d for d in lookalike_decisions().values()):
        return rows  # never overwrite a sheet that already contains reviewer decisions
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(LOOKALIKE_FIELDS)
        for r in sorted(rows, key=lambda r: r["text"]):
            w.writerow([r["item_id"], r["split"], r["text"], r["label_source"].split(":", 1)[1],
                        "ABSTAIN (outside the 60 catalogue types)", "", ""])
    return rows


def lookalike_decisions():
    """item_id -> reviewer decision ('' if not yet reviewed)."""
    path = os.path.join(PILOT, "p7_lookalike_confirmation.csv")
    if not os.path.exists(path):
        return {}
    return {r["item_id"]: r[LOOKALIKE_FIELDS[5]].strip().lower() for r in read_csv(path)}
