"""Human review materials (v4, 15 Nov 2026) and the authoritative P7 review treatments (Phase A, 24 Nov 2026).

1. Ten-item pilot: a sanity check of the labelling RULES by one reviewer (Author 1). The reviewer never sees
   system outputs. Items P01-P05 and P07-P10 are pinned to the items drawn in v3 (continuity with the
   authors' Phase 6 review). P06 is redrawn (seeded) from the licensed Unicode P7 look-alike pool, because
   the Open Products Facts source was withdrawn.
2. P7 look-alike confirmation (16 items) and P7 plain-name scan (100 names). The reviewer's decisions are
   recorded in `p7_lookalike_review_v4.csv` and `p7_plain_scan_progress_v4.csv`. These records are READ ONLY.
3. Authoritative treatments: `authorised_review_treatments_v1.csv` lists every P7 item exactly once with its
   recorded decision and the authorised treatment (keep / exclude). It is the ONLY input the benchmark builder
   uses to remove P7 items. It is validated against the two review records before every use:
       look-alike  Outside                                -> keep
       look-alike  Uncertain / Potentially in catalogue   -> exclude
       plain scan  Clear                                  -> keep
       plain scan  Flag for review / Exception            -> exclude
   Every exclusion needs an explicit reason, authoriser, ISO date and authorisation record.

Review-sheet writers never overwrite an existing file, whatever its content or status line.
The scan file's `REVIEWED:` line is no longer read by any code.
"""
import csv
import datetime
import hashlib
import os
from collections import Counter

from lexitax_v2.reference import ISO_TO_TABLE

from .build_common import read_csv
from .paths import GEN, PILOT
from .perturb import rng_for
from .refdata import load_hs6

PILOT_FILE = "pilot_review_sheet_v4.csv"
LOOKALIKE_FILE = "p7_lookalike_review_v4.csv"
PLAIN_FILE = "p7_plain_scan_v4.txt"
PLAIN_PROGRESS_FILE = "p7_plain_scan_progress_v4.csv"
TREATMENTS_FILE = "authorised_review_treatments_v1.csv"

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


def _write_new(path, write):
    """Create `path` with `write(fh)` only if it does not exist. Returns True if written, False if kept.
    Mode 'x' makes the no-overwrite rule atomic: an existing review file is never truncated."""
    try:
        fh = open(path, "x", encoding="utf-8", newline="")
    except FileExistsError:
        return False
    with fh:
        write(fh)
    return True


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


def build_pilot(seed, pilot_dir=None):
    pilot_dir = pilot_dir or PILOT
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
    os.makedirs(pilot_dir, exist_ok=True)

    def write(fh):
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    _write_new(os.path.join(pilot_dir, PILOT_FILE), write)  # an existing sheet is never overwritten
    return rows


LOOKALIKE_FIELDS = ["item_id", "input_text", "unicode_group_subgroup", "possibly_confused_with_catalogue_type",
                    "question", "reviewer_decision(Outside/Potentially in catalogue/Uncertain)", "reviewer_comments"]
QUESTION = "Is this genuinely outside the supported 60-product catalogue?"


def build_lookalike_sheet(pilot_dir=None):
    pilot_dir = pilot_dir or PILOT
    rows = sorted((r for r in read_csv(os.path.join(GEN, "product_benchmark.csv"))
                   if r["subset"] == "P7_outside" and r["look_alike"] == "True"), key=lambda r: r["text"].lower())
    os.makedirs(pilot_dir, exist_ok=True)

    def write(fh):
        w = csv.writer(fh)
        w.writerow(LOOKALIKE_FIELDS)
        for r in rows:
            w.writerow([r["item_id"], r["text"], r["label_source"].split(":", 1)[1],
                        r["label_base_types"].replace(";", "; "), QUESTION, "", ""])
    _write_new(os.path.join(pilot_dir, LOOKALIKE_FILE), write)  # never overwritten, even if undecided
    return rows


def build_plain_scan_sheet(pilot_dir=None):
    """Checklist of P7 plain names for the reviewer. Written only if the file does not exist yet; an existing
    file is never overwritten, whatever its `REVIEWED:` line says. Decisions are recorded in
    p7_plain_scan_progress_v4.csv and applied only through the authoritative treatments file."""
    pilot_dir = pilot_dir or PILOT
    rows = sorted((r for r in read_csv(os.path.join(GEN, "product_benchmark.csv"))
                   if r["subset"] == "P7_outside" and r["look_alike"] != "True"), key=lambda r: r["text"].lower())
    os.makedirs(pilot_dir, exist_ok=True)

    def write(fh):
        fh.write("# P7 plain names (Unicode emoji short names). Question for each: could this be one of the 60\n"
                 "# catalogue product types (see catalogue_base_types.csv)? Write any such names, one per line,\n"
                 "# BELOW the line 'EXCEPTIONS:'. Then replace 'REVIEWED: no' with 'REVIEWED: yes <name> <date>'.\n#\n")
        for r in rows:
            fh.write(f"#   {r['text']}\n")
        fh.write("REVIEWED: no\nEXCEPTIONS:\n")
    _write_new(os.path.join(pilot_dir, PLAIN_FILE), write)
    return rows


# ---------------------------------------------------------------------------------------------------------
# Authoritative P7 review treatments
# ---------------------------------------------------------------------------------------------------------
class ReviewTreatmentError(ValueError):
    """The decisions file is missing, incomplete, duplicated or contradicts the review records."""


PLAIN_PROGRESS_DECISION = "reviewer_decision(Clear/Exception)"
TREATMENT_FIELDS = ["item_id", "text", "split", "look_alike", "review_source", "review_file", "review_item_no",
                    "recorded_decision", "authorised_treatment", "reason", "authorised_by", "authorised_on",
                    "authorisation_record"]
REVIEW_SOURCES = {"lookalike_v4": f"pilot/{LOOKALIKE_FILE}", "plain_scan_v4": f"pilot/{PLAIN_PROGRESS_FILE}"}
# Pre-declared mapping from a recorded reviewer decision to the only permitted treatment.
REQUIRED_TREATMENT = {
    ("lookalike_v4", "Outside"): "keep",
    ("lookalike_v4", "Uncertain"): "exclude",
    ("lookalike_v4", "Potentially in catalogue"): "exclude",
    ("plain_scan_v4", "Clear"): "keep",
    ("plain_scan_v4", "Flag for review"): "exclude",
    ("plain_scan_v4", "Exception"): "exclude",
}
AUDIT_FIELDS = ["exclusion_reason", "decision_source", "review_item_no", "recorded_decision", "authorised_by",
                "authorised_on", "authorisation_record"]


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def review_records(pilot_dir=None):
    """item_id -> {source, item_no, text, decision} from the two P7 review records (read only).
    Look-alike items are numbered 1..16 in sheet order (the order in which they were reviewed)."""
    pilot_dir = pilot_dir or PILOT
    recs, problems = {}, []
    for no, r in enumerate(read_csv(os.path.join(pilot_dir, LOOKALIKE_FILE)), 1):
        entry = {"source": "lookalike_v4", "item_no": no, "text": r["input_text"],
                 "decision": (r[LOOKALIKE_FIELDS[5]] or "").strip()}
        if r["item_id"] != f"P7_outside|{r['input_text']}":
            problems.append(f"look-alike record #{no}: item_id {r['item_id']!r} does not match its text")
        if r["item_id"] in recs:
            problems.append(f"review records list {r['item_id']!r} more than once")
        recs[r["item_id"]] = entry
    for r in read_csv(os.path.join(pilot_dir, PLAIN_PROGRESS_FILE)):
        iid = f"P7_outside|{r['name']}"
        if iid in recs:
            problems.append(f"review records list {iid!r} more than once")
        recs[iid] = {"source": "plain_scan_v4", "item_no": int(r["item_no"]), "text": r["name"],
                     "decision": (r[PLAIN_PROGRESS_DECISION] or "").strip()}
    if problems:
        raise ReviewTreatmentError("; ".join(problems))
    return recs


def _is_iso_date(s):
    try:
        datetime.date.fromisoformat(s)
        return True
    except (TypeError, ValueError):
        return False


def validate_treatments(header, rows, records):
    """Return a list of problems (empty = valid). `rows` are dicts keyed by TREATMENT_FIELDS."""
    errs = []
    if header != TREATMENT_FIELDS:
        errs.append(f"header must be exactly {TREATMENT_FIELDS}, got {header}")
        return errs
    counts = Counter(r["item_id"] for r in rows)
    for iid, n in sorted(counts.items()):
        if n > 1:
            errs.append(f"{iid}: listed {n} times (duplicate decision)")
    for iid in sorted(set(records) - set(counts)):
        errs.append(f"{iid}: reviewed item missing from the decisions file")
    for r in rows:
        iid = r["item_id"]
        rec = records.get(iid)
        if rec is None:
            errs.append(f"{iid}: not an item in the review records")
            continue
        if not rec["decision"]:
            errs.append(f"{iid}: the review record has no decision (review incomplete)")
        if r["review_source"] != rec["source"]:
            errs.append(f"{iid}: review_source {r['review_source']!r} contradicts the record ({rec['source']})")
        if r["review_file"] != REVIEW_SOURCES.get(r["review_source"]):
            errs.append(f"{iid}: review_file {r['review_file']!r} does not match review_source")
        if r["review_item_no"] != str(rec["item_no"]):
            errs.append(f"{iid}: review_item_no {r['review_item_no']!r} contradicts the record (#{rec['item_no']})")
        if r["text"] != rec["text"]:
            errs.append(f"{iid}: text {r['text']!r} contradicts the record ({rec['text']!r})")
        if r["look_alike"] != ("True" if rec["source"] == "lookalike_v4" else "False"):
            errs.append(f"{iid}: look_alike {r['look_alike']!r} contradicts the review source")
        if r["split"] not in ("dev", "test"):
            errs.append(f"{iid}: split must be dev or test")
        if r["recorded_decision"] != rec["decision"]:
            errs.append(f"{iid}: recorded_decision {r['recorded_decision']!r} contradicts the record "
                        f"({rec['decision']!r})")
        t = r["authorised_treatment"]
        if t not in ("keep", "exclude"):
            errs.append(f"{iid}: authorised_treatment must be keep or exclude, got {t!r}")
        required = REQUIRED_TREATMENT.get((rec["source"], rec["decision"]))
        if rec["decision"] and required is None:
            errs.append(f"{iid}: recorded decision {rec['decision']!r} has no pre-declared treatment")
        elif required and t in ("keep", "exclude") and t != required:
            errs.append(f"{iid}: '{rec['decision']}' must be '{required}', not '{t}'")
        if not r["reason"].strip():
            errs.append(f"{iid}: reason is empty")
        if t == "exclude":
            for f in ("authorised_by", "authorisation_record"):
                if not r[f].strip():
                    errs.append(f"{iid}: exclusion lacks {f}")
            if not _is_iso_date(r["authorised_on"]):
                errs.append(f"{iid}: exclusion lacks a valid authorised_on date (YYYY-MM-DD)")
    return errs


def load_treatments(path=None, pilot_dir=None):
    """Read, validate and return {item_id: row}. Raises ReviewTreatmentError on any problem."""
    pilot_dir = pilot_dir or PILOT
    path = path or os.path.join(pilot_dir, TREATMENTS_FILE)
    if not os.path.exists(path):
        raise ReviewTreatmentError(f"authoritative decisions file not found: {path}")
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        header = list(reader.fieldnames or [])
        rows = list(reader)
    errs = validate_treatments(header, rows, review_records(pilot_dir))
    if errs:
        raise ReviewTreatmentError(f"{path}: {len(errs)} problem(s):\n  - " + "\n  - ".join(errs))
    return {r["item_id"]: r for r in rows}


def apply_review_treatments(items, treatments, log, audit=None):
    """Remove the authorised P7 exclusions from finalised benchmark rows.

    Every generated P7 item must appear in `treatments` exactly once and vice versa, with matching text,
    look-alike flag and split; otherwise ReviewTreatmentError. Excluded rows are logged as
    ('review_exclusion', ...) and appended in full to `audit` with the AUDIT_FIELDS."""
    p7 = {it["item_id"]: it for it in items if it["subset"] == "P7_outside"}
    errs = [f"{i}: generated P7 item has no decision" for i in sorted(set(p7) - set(treatments))]
    errs += [f"{i}: decision for an item that was not generated" for i in sorted(set(treatments) - set(p7))]
    for iid in sorted(set(p7) & set(treatments)):
        it, t = p7[iid], treatments[iid]
        if (it["text"], str(it["look_alike"]), it["split"]) != (t["text"], t["look_alike"], t["split"]):
            errs.append(f"{iid}: text/look_alike/split differ between the build and the decisions file")
    if errs:
        raise ReviewTreatmentError("decisions file does not match the generated P7 items:\n  - " + "\n  - ".join(errs))
    out = []
    for it in items:
        t = treatments.get(it["item_id"]) if it["subset"] == "P7_outside" else None
        if t is None or t["authorised_treatment"] == "keep":
            out.append(it)
            continue
        log.append(("review_exclusion", f"{it['item_id']} | {t['review_source']} #{t['review_item_no']} | "
                                        f"{t['recorded_decision']} | {t['reason']}"))
        if audit is not None:
            audit.append(dict(it, exclusion_reason=t["reason"], decision_source=t["review_file"],
                              review_item_no=t["review_item_no"], recorded_decision=t["recorded_decision"],
                              authorised_by=t["authorised_by"], authorised_on=t["authorised_on"],
                              authorisation_record=t["authorisation_record"]))
    return out


def provenance_log_entries(pilot_dir=None, path=None):
    """Build-log entries fixing the exact decisions file and review records used for a build."""
    pilot_dir = pilot_dir or PILOT
    path = path or os.path.join(pilot_dir, TREATMENTS_FILE)
    return [("review_treatments_file", f"{TREATMENTS_FILE} sha256={sha256_file(path)}"),
            ("review_record", f"{LOOKALIKE_FILE} sha256={sha256_file(os.path.join(pilot_dir, LOOKALIKE_FILE))}"),
            ("review_record",
             f"{PLAIN_PROGRESS_FILE} sha256={sha256_file(os.path.join(pilot_dir, PLAIN_PROGRESS_FILE))}")]
