"""Human review materials (v4, 15 Nov 2026).

1. Ten-item pilot: a sanity check of the labelling RULES by one reviewer (Author 1). The reviewer never sees
   system outputs. Items P01-P05 and P07-P10 are pinned to the items drawn in v3 (continuity with the
   authors' Phase 6 review). P06 is redrawn (seeded) from the licensed Unicode P7 look-alike pool, because
   the Open Products Facts source was withdrawn.
2. P7 look-alike confirmation: every Unicode emoji name in P7 that shares a word with a catalogue type.
   Pre-declared rule: only items marked 'outside' are kept; 'potentially_in_catalogue' and 'uncertain'
   items are removed before freezing (logged).
Existing sheets that already contain reviewer decisions are never overwritten.
"""
import csv
import os

from lexitax_v2.reference import ISO_TO_TABLE

from .build_common import read_csv
from .paths import GEN, PILOT
from .perturb import rng_for
from .refdata import load_hs6

PILOT_FILE = "pilot_review_sheet_v4.csv"
LOOKALIKE_FILE = "p7_lookalike_review_v4.csv"

PINNED = [  # (pilot id, item_id, category shown to the reviewer, difficulty)
    ("P01", "P2_format|Scanner|ws_punct", "Formatting variation", "easy"),
    ("P02", "P3_typo|Graphics Card|typo|0", "Spelling mistake", "borderline"),
    ("P03", "P4_short|WiFi Adapter|head_noun", "Underspecified short form (qualifier removed)", "ambiguous"),
    ("P04", "P5_confusable|Memory Card|typo_distinguishing_word", "Similar but distinct product", "borderline"),
    ("P05", "P6_ambiguous|word|computer", "Ambiguous word", "ambiguous"),
    ("P06", None, "Outside catalogue, look-alike name", "unsupported"),
    ("P07", "P8_hs|other_chapter|080122", "Formal HS text, unrelated chapter", "out-of-domain"),
    ("P08", "CD|NZ|es", "Foreign-language country name", "borderline"),
    ("P09", "CB|DZ|official_name", "Real country without tax data", "unsupported"),
    ("P10", "CE|sint", "Ambiguous country word", "ambiguous"),
]

FIELDS = ["pilot_id", "category", "difficulty", "input_text", "gold_answer", "expected_system_behaviour",
          "source_and_reference", "label_explanation", "what_to_verify",
          "reviewer_decision(Accept/Reject/Uncertain)", "reviewer_comments", "minutes_spent"]


def _has_decisions(path, col):
    if not os.path.exists(path):
        return False
    return any((r.get(col) or "").strip() for r in read_csv(path))


def _describe(r, hs6):
    """Return (gold, behaviour, source, explanation, verify) for a benchmark row."""
    if "gold_iso" in r:  # country item
        iso = r["gold_iso"]
        if iso:
            avail = r["tax_data_available"] == "True"
            gold = f"Country = {iso}" + (f" ({ISO_TO_TABLE[iso]})" if iso in ISO_TO_TABLE else "")
            beh = ("Identify " + iso + ", then COMPUTE with its tax rates" if avail else
                   "Identify " + iso + ", then REFUSE the tax calculation (no tax data in taxes.csv)")
            if r["s1_builtin"] != "True":
                beh += ". This spelling is NOT in S1's ISO lookup table, so S1 declining is SAFE but counted as over-abstention, not correct"
        else:
            gold, beh = "No single country", "Do NOT identify a country; REFUSE"
        return gold, beh, r["label_source"], "", ""
    if r["expected"] == "ANSWER":
        gold = f"Catalogue type '{r['label_base_types']}'" if r["label_base_types"] else f"HS {r['label_hs']}"
        return gold, "ANSWER with that type", r["label_source"], "", ""
    return "None of the 60 catalogue types", "DECLINE (abstain)", r["label_source"], "", ""


def build_pilot(seed):
    hs6, _ = load_hs6()
    prod = {r["item_id"]: r for r in read_csv(os.path.join(GEN, "product_benchmark.csv"))}
    ctry = {r["item_id"]: r for r in read_csv(os.path.join(GEN, "country_benchmark.csv"))}
    look = sorted((r for r in prod.values() if r["subset"] == "P7_outside" and r["look_alike"] == "True"),
                  key=lambda r: r["item_id"])
    rows = []
    for pid, iid, cat, diff in PINNED:
        if iid is None:
            r = rng_for(seed, "pilot-v4", pid).choice(look)
        else:
            r = prod.get(iid) or ctry.get(iid)
            if r is None:
                raise KeyError(f"pinned pilot item missing from draft benchmark: {iid}")
        gold, beh, src, _, _ = _describe(r, hs6)
        rows.append({"pilot_id": pid, "category": cat, "difficulty": diff, "input_text": r["text"],
                     "gold_answer": gold, "expected_system_behaviour": beh,
                     "source_and_reference": f"{src} [item {r['item_id']}, split {r['split']}]",
                     "label_explanation": "see pilot_review_sheet.md", "what_to_verify": "see pilot_review_sheet.md"})
    os.makedirs(PILOT, exist_ok=True)
    path = os.path.join(PILOT, PILOT_FILE)
    if _has_decisions(path, FIELDS[9]):
        return rows  # never overwrite reviewer decisions
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    return rows


LOOKALIKE_FIELDS = ["item_id", "input_text", "unicode_group_subgroup", "possibly_confused_with_catalogue_type",
                    "question", "reviewer_decision(Outside/Potentially in catalogue/Uncertain)", "reviewer_comments"]
QUESTION = "Is this genuinely outside the supported 60-product catalogue?"


def build_lookalike_sheet():
    rows = sorted((r for r in read_csv(os.path.join(GEN, "product_benchmark.csv"))
                   if r["subset"] == "P7_outside" and r["look_alike"] == "True"), key=lambda r: r["text"].lower())
    os.makedirs(PILOT, exist_ok=True)
    path = os.path.join(PILOT, LOOKALIKE_FILE)
    if _has_decisions(path, LOOKALIKE_FIELDS[5]):
        return rows
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(LOOKALIKE_FIELDS)
        for r in rows:
            w.writerow([r["item_id"], r["text"], r["label_source"].split(":", 1)[1],
                        r["label_base_types"].replace(";", "; "), QUESTION, "", ""])
    return rows


def lookalike_decisions():
    """item_id -> normalised reviewer decision: 'outside' | 'potentially in catalogue' | 'uncertain' | ''."""
    path = os.path.join(PILOT, LOOKALIKE_FILE)
    if not os.path.exists(path):
        return {}
    return {r["item_id"]: (r[LOOKALIKE_FIELDS[5]] or "").strip().lower() for r in read_csv(path)}


PLAIN_FILE = "p7_plain_scan_v4.txt"


def build_plain_scan_sheet():
    """Checklist of P7 plain names. The reviewer lists (below the marker line) any name that could be one of the
    60 catalogue types; listed names are removed before freezing. The file is never overwritten once edited."""
    rows = sorted((r for r in read_csv(os.path.join(GEN, "product_benchmark.csv"))
                   if r["subset"] == "P7_outside" and r["look_alike"] != "True"), key=lambda r: r["text"].lower())
    path = os.path.join(PILOT, PLAIN_FILE)
    if os.path.exists(path) and plain_exceptions() is not None:
        return rows
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# P7 plain names (Unicode emoji short names). Question for each: could this be one of the 60\n"
                 "# catalogue product types (see catalogue_base_types.csv)? Write any such names, one per line,\n"
                 "# BELOW the line 'EXCEPTIONS:'. Then replace 'REVIEWED: no' with 'REVIEWED: yes <name> <date>'.\n#\n")
        for r in rows:
            fh.write(f"#   {r['text']}\n")
        fh.write("REVIEWED: no\nEXCEPTIONS:\n")
    return rows


def plain_exceptions():
    """None if the scan is not yet reviewed; otherwise the set of canonical names flagged by the reviewer."""
    from lexitax_v2.normalize import canonical
    path = os.path.join(PILOT, PLAIN_FILE)
    if not os.path.exists(path):
        return None
    lines = open(path, encoding="utf-8").read().splitlines()
    if not any(ln.startswith("REVIEWED: yes") for ln in lines):
        return None
    after = lines[[i for i, ln in enumerate(lines) if ln.startswith("EXCEPTIONS:")][0] + 1:]
    return {canonical(ln) for ln in after if ln.strip() and not ln.startswith("#")}
