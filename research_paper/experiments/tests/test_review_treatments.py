"""Phase A (IMPLEMENTATION_PLAN.md): authoritative P7 review treatments, builder, audit file, sheet
protection and freeze guard.

Every build in this module runs into pytest temporary directories, using COPIES of the review records.
The committed generated benchmark, the original review records and pilot/ are only read, never written.
"""
import csv
import hashlib
import json
import os
import shutil

import pytest
from _helpers import csv_rows, without_items
from _original import (AUTHORISED_P7_EXCLUSIONS, ORIGINAL_COMMIT, assert_expected_live_state, original_product_bytes,
                       original_product_rows)

import run_all
from lexeval import build_products, pilot
from lexeval.build_common import read_csv, write_csv
from lexeval.paths import GEN, PILOT, config
from lexeval.pilot import ReviewTreatmentError

AUTHORISED_EXCLUSIONS = {
    "P7_outside|couch and lamp": ("lookalike_v4", "4", "Uncertain", "dev"),
    "P7_outside|toothbrush": ("lookalike_v4", "14", "Uncertain", "test"),
    "P7_outside|video game": ("lookalike_v4", "15", "Uncertain", "dev"),
    "P7_outside|satellite antenna": ("plain_scan_v4", "81", "Flag for review", "test"),
}
# SHA-256 of the original review records as committed before Phase A (verified 24 Nov 2026). They must never change.
ORIGINAL_RECORDS = {
    "p7_lookalike_review_v4.csv": "d89a5ffe189001d34c757d94b78d13ac296cf346150b629cf5939543118fbdf3",
    "p7_plain_scan_v4.txt": "efb6916041092a7644110268a0a4ff6d19adac3a6d2c3c55cd460b8bfb48a637",
    "p7_plain_scan_progress_v4.csv": "185879b047ca1a367c3798e4a768f82679d253018173e48c991896ce0a13a30c",
    "pilot_review_sheet_v4.csv": "ec8e11edff4fbec412d771822e85e7e2039a165110a1bd6549ee36fd4d00356c",
    "pilot_reviewed_items.json": "ce958c65996b1b7312ca621a55aaddc5e6d956e2916507c6902480e7ba4b384e",
    "catalogue_base_types.csv": "2e750410055aa9a7b1b35cb1c21514ca660657b28c80f0907a44fc62f6c597e2",
}
# Phase D step 0: "the original draft" is the immutable benchmark from git commit a0129b8 (tests/_original.py),
# never the live data/generated/product_benchmark.csv, which the production rebuild replaces.


def _sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _pilot_copy(dst):
    shutil.copytree(PILOT, dst, ignore=shutil.ignore_patterns("superseded"))
    return str(dst)


def _treatment_rows(path=None):
    with open(path or os.path.join(PILOT, pilot.TREATMENTS_FILE), encoding="utf-8", newline="") as fh:
        r = csv.DictReader(fh)
        return list(r.fieldnames), list(r)


def _write_treatments(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        w.writerows(rows)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """One authoritative build into a temporary directory (product benchmark, audit rows, build log)."""
    pdir = _pilot_copy(tmp_path_factory.mktemp("b") / "pilot")
    log, audit = [], []
    items = build_products.build(config(), log, audit=audit, pilot_dir=pdir)
    out = tmp_path_factory.mktemp("gen")
    write_csv(str(out / "product_benchmark.csv"), items, build_products.FIELDS)
    write_csv(str(out / run_all.EXCLUDED_FILE), audit, build_products.EXCLUDED_FIELDS)
    with open(out / "build_log.json", "w", encoding="utf-8") as fh:
        json.dump(log, fh, indent=1)
    # Phase B: the freeze guard also validates the TEST evaluation exclusions, which need the country benchmark
    # (unchanged by Phase A, so a byte copy of the committed file).
    shutil.copy(os.path.join(GEN, "country_benchmark.csv"), out / "country_benchmark.csv")
    return {"items": items, "audit": audit, "log": log, "gen": out, "pilot": pdir}


# ----------------------------------------------------------------------------------------------- decisions file
def test_decisions_file_is_complete_and_valid():
    tre = pilot.load_treatments()  # raises on any problem
    assert len(tre) == 116
    recs = pilot.review_records()
    assert set(tre) == set(recs) and len(recs) == 116


def test_exact_treatments_for_all_116_items():
    header, rows = _treatment_rows()
    by = {}
    for r in rows:
        by.setdefault((r["review_source"], r["recorded_decision"], r["authorised_treatment"]), []).append(r["item_id"])
    assert {k: len(v) for k, v in by.items()} == {
        ("lookalike_v4", "Outside", "keep"): 13,
        ("lookalike_v4", "Uncertain", "exclude"): 3,
        ("plain_scan_v4", "Clear", "keep"): 99,
        ("plain_scan_v4", "Flag for review", "exclude"): 1,
    }
    excl = {r["item_id"]: (r["review_source"], r["review_item_no"], r["recorded_decision"], r["split"])
            for r in rows if r["authorised_treatment"] == "exclude"}
    assert excl == AUTHORISED_EXCLUSIONS
    for r in rows:
        assert r["reason"].strip()
        if r["authorised_treatment"] == "exclude":
            assert r["authorised_by"].strip() and r["authorisation_record"].strip()
            assert r["authorised_on"] == "2026-11-24"
            assert f"#{r['review_item_no']} recorded '{r['recorded_decision']}'" in r["reason"]


def test_decisions_match_every_review_record_and_draft_item():
    """Each decision row agrees with its review record and with the ORIGINAL draft P7 row (from a0129b8)."""
    _, rows = _treatment_rows()
    recs = pilot.review_records()
    draft = {r["item_id"]: r for r in original_product_rows() if r["subset"] == "P7_outside"}
    assert set(draft) == {r["item_id"] for r in rows}
    for r in rows:
        rec, d = recs[r["item_id"]], draft[r["item_id"]]
        assert (r["review_source"], r["review_item_no"], r["text"], r["recorded_decision"]) == \
            (rec["source"], str(rec["item_no"]), rec["text"], rec["decision"])
        assert (r["text"], r["look_alike"], r["split"]) == (d["text"], d["look_alike"], d["split"])


# --------------------------------------------------------------------------------- validation failure modes
def _errs(mutate):
    header, rows = _treatment_rows()
    rows = [dict(r) for r in rows]
    header, rows = mutate(header, rows) or (header, rows)
    return pilot.validate_treatments(header, rows, pilot.review_records())


def _row(rows, iid):
    return next(r for r in rows if r["item_id"] == iid)


def test_valid_file_has_no_errors():
    assert _errs(lambda h, rs: None) == []


def test_missing_item_fails():
    errs = _errs(lambda h, rs: (h, [r for r in rs if r["item_id"] != "P7_outside|sandwich"]))
    assert any("sandwich" in e and "missing" in e for e in errs)


def test_missing_exclusion_row_fails():
    errs = _errs(lambda h, rs: (h, [r for r in rs if r["item_id"] != "P7_outside|toothbrush"]))
    assert any("toothbrush" in e and "missing" in e for e in errs)


def test_duplicated_item_fails():
    errs = _errs(lambda h, rs: (h, rs + [dict(_row(rs, "P7_outside|sandwich"))]))
    assert any("sandwich" in e and "duplicate" in e for e in errs)


def test_unknown_item_id_fails():
    def m(h, rs):
        _row(rs, "P7_outside|sandwich")["item_id"] = "P7_outside|sandwich maker"
    errs = _errs(m)
    assert any("sandwich maker" in e and "not an item" in e for e in errs)
    assert any("P7_outside|sandwich:" in e and "missing" in e for e in errs)


@pytest.mark.parametrize("field,value,needle", [
    ("recorded_decision", "Outside", "recorded_decision"),       # Uncertain recorded -> claim Outside
    ("review_item_no", "5", "review_item_no"),
    ("review_source", "plain_scan_v4", "review_source"),
    ("text", "tooth brush", "text"),
    ("look_alike", "False", "look_alike"),
    ("review_file", "pilot/p7_plain_scan_v4.txt", "review_file"),
])
def test_contradicting_the_review_record_fails(field, value, needle):
    def m(h, rs):
        _row(rs, "P7_outside|toothbrush")[field] = value
    assert any("toothbrush" in e and needle in e for e in _errs(m))


@pytest.mark.parametrize("iid,treatment", [
    ("P7_outside|credit card", "exclude"),        # Outside look-alike wrongly excluded
    ("P7_outside|sandwich", "exclude"),           # Clear plain name wrongly excluded
    ("P7_outside|video game", "keep"),            # Uncertain look-alike wrongly retained
    ("P7_outside|satellite antenna", "keep"),     # Flag-for-review item wrongly retained
])
def test_wrong_treatment_fails(iid, treatment):
    def m(h, rs):
        _row(rs, iid)["authorised_treatment"] = treatment
    errs = _errs(m)
    assert any(iid in e and "must be" in e for e in errs)


@pytest.mark.parametrize("field,value", [
    ("reason", " "), ("authorised_by", ""), ("authorisation_record", ""), ("authorised_on", ""),
    ("authorised_on", "24/11/2026"),
])
def test_exclusion_without_authorisation_or_reason_fails(field, value):
    def m(h, rs):
        _row(rs, "P7_outside|couch and lamp")[field] = value
    errs = _errs(m)
    assert any("couch and lamp" in e and field in e for e in errs)


def test_unknown_treatment_value_and_bad_header_fail():
    def m(h, rs):
        _row(rs, "P7_outside|sandwich")["authorised_treatment"] = "drop"
    assert any("keep or exclude" in e for e in _errs(m))
    assert any("header" in e for e in _errs(lambda h, rs: (h[:-1], rs)))


def test_incomplete_review_record_fails(tmp_path):
    """A review record without a decision cannot be satisfied by any treatment."""
    pdir = _pilot_copy(tmp_path / "pilot")
    path = os.path.join(pdir, pilot.LOOKALIKE_FILE)
    rows = csv_rows(open(path, "rb").read())
    rows[1][5] = ""  # first look-alike: decision blanked (copy only)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerows(rows)
    with pytest.raises(ReviewTreatmentError, match="review incomplete"):
        pilot.load_treatments(pilot_dir=pdir)


# ------------------------------------------------------------------------------------- builder behaviour
def test_builder_excludes_exactly_the_four_authorised_items(built):
    ids = {r["item_id"] for r in built["items"]}
    assert not set(AUTHORISED_EXCLUSIONS) & ids
    assert {r["item_id"] for r in built["audit"]} == set(AUTHORISED_EXCLUSIONS)
    p7 = [r for r in built["items"] if r["subset"] == "P7_outside"]
    assert len(p7) == 112 and len(built["items"]) == 805


def test_all_retained_items_present_with_gold_decline(built):
    _, rows = _treatment_rows()
    keep = {r["item_id"] for r in rows if r["authorised_treatment"] == "keep"}
    p7 = {r["item_id"]: r for r in built["items"] if r["subset"] == "P7_outside"}
    assert set(p7) == keep and len(keep) == 112
    assert all(p7[i]["expected"] == "ABSTAIN" and p7[i]["abstain_reason"] == "outside_catalogue" for i in keep)
    assert sum(str(p7[i]["look_alike"]) == "True" for i in keep) == 13


def test_build_equals_draft_minus_exactly_four_rows(built):
    """Exact-difference check in a temporary directory: every other row is byte-identical to the ORIGINAL draft
    (from a0129b8), whatever state the live benchmark is in."""
    got = (built["gen"] / "product_benchmark.csv").read_bytes()
    assert set(AUTHORISED_EXCLUSIONS) == AUTHORISED_P7_EXCLUSIONS
    assert got == without_items(original_product_bytes(), AUTHORISED_EXCLUSIONS)


def test_audit_file_holds_full_original_rows_and_reasons(built):
    draft = {r[0]: r for r in csv_rows(original_product_bytes())[1:]}   # original rows from a0129b8
    audit = csv_rows((built["gen"] / run_all.EXCLUDED_FILE).read_bytes())
    assert audit[0] == build_products.EXCLUDED_FIELDS
    _, rows = _treatment_rows()
    tre = {r["item_id"]: r for r in rows}
    assert len(audit) - 1 == 4
    n = len(build_products.FIELDS)
    for row in audit[1:]:
        iid = row[0]
        assert row[:n] == draft[iid], f"{iid}: audit row differs from the original draft row"
        extra = dict(zip(build_products.EXCLUDED_FIELDS[n:], row[n:]))
        t = tre[iid]
        assert extra == {"exclusion_reason": t["reason"], "decision_source": t["review_file"],
                         "review_item_no": t["review_item_no"], "recorded_decision": t["recorded_decision"],
                         "authorised_by": t["authorised_by"], "authorised_on": t["authorised_on"],
                         "authorisation_record": t["authorisation_record"]}
        assert extra["exclusion_reason"].strip()


def test_every_exclusion_is_logged(built):
    excl = [e for e in built["log"] if e[0] == "review_exclusion"]
    assert len(excl) == 4
    for kind, msg in excl:
        iid, src, decision, reason = msg.split(" | ", 3)
        source, no, rec, _ = AUTHORISED_EXCLUSIONS[iid]
        assert (src, decision) == (f"{source} #{no}", rec) and reason.strip()
    assert ("review_treatments_file",
            f"{pilot.TREATMENTS_FILE} sha256={_sha(os.path.join(PILOT, pilot.TREATMENTS_FILE))}") in built["log"]
    assert not [e for e in built["log"] if e[0] in ("lookalike_removed_after_review", "plain_removed_after_review")]


def test_build_is_deterministic_and_ignores_scan_status(built, tmp_path):
    """A second build in another temporary directory is byte-identical, even when the obsolete scan file
    claims 'REVIEWED: yes' with an exception: the builder reads only the authoritative decisions file."""
    pdir = _pilot_copy(tmp_path / "pilot")
    with open(os.path.join(pdir, pilot.PLAIN_FILE), "a", encoding="utf-8") as fh:  # copy only
        fh.write("REVIEWED: yes test 2026-11-24\nEXCEPTIONS:\nsandwich\n")
    log, audit = [], []
    items = build_products.build(config(), log, audit=audit, pilot_dir=pdir)
    write_csv(str(tmp_path / "p.csv"), items, build_products.FIELDS)
    write_csv(str(tmp_path / "x.csv"), audit, build_products.EXCLUDED_FIELDS)
    assert (tmp_path / "p.csv").read_bytes() == (built["gen"] / "product_benchmark.csv").read_bytes()
    assert (tmp_path / "x.csv").read_bytes() == (built["gen"] / run_all.EXCLUDED_FILE).read_bytes()
    assert log == built["log"]


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "contradiction", "absent_file"])
def test_builder_stops_on_bad_decisions(tmp_path, mutation):
    pdir = _pilot_copy(tmp_path / "pilot")
    path = os.path.join(pdir, pilot.TREATMENTS_FILE)
    header, rows = _treatment_rows(path)
    if mutation == "missing":
        rows = [r for r in rows if r["item_id"] != "P7_outside|satellite antenna"]
    elif mutation == "duplicate":
        rows.append(dict(rows[0]))
    elif mutation == "contradiction":
        _row(rows, "P7_outside|toothbrush")["authorised_treatment"] = "keep"
    if mutation == "absent_file":
        os.remove(path)
    else:
        _write_treatments(path, header, rows)
    with pytest.raises(ReviewTreatmentError):
        build_products.build(config(), [], audit=[], pilot_dir=pdir)


def _syn(iid, text, la, split="test", subset="P7_outside"):
    return {"item_id": iid, "subset": subset, "text": text, "look_alike": la, "split": split}


def _syn_t(iid, text, la, treatment, split="test"):
    return {"item_id": iid, "text": text, "look_alike": str(la), "split": split, "authorised_treatment": treatment,
            "review_source": "lookalike_v4", "review_item_no": "1", "recorded_decision": "Uncertain",
            "reason": "r", "review_file": "f", "authorised_by": "a", "authorised_on": "2026-11-24",
            "authorisation_record": "rec"}


def test_apply_treatments_rejects_generated_item_without_decision():
    items = [_syn("P7_outside|a", "a", True), _syn("P7_outside|b", "b", False), _syn("P1|x", "x", "", subset="P1")]
    with pytest.raises(ReviewTreatmentError, match="has no decision"):
        pilot.apply_review_treatments(items, {"P7_outside|a": _syn_t("P7_outside|a", "a", True, "keep")}, [])


def test_apply_treatments_rejects_decision_for_item_not_generated():
    items = [_syn("P7_outside|a", "a", True)]
    tre = {"P7_outside|a": _syn_t("P7_outside|a", "a", True, "keep"),
           "P7_outside|z": _syn_t("P7_outside|z", "z", True, "exclude")}
    with pytest.raises(ReviewTreatmentError, match="not generated"):
        pilot.apply_review_treatments(items, tre, [])


def test_apply_treatments_rejects_text_or_split_mismatch():
    items = [_syn("P7_outside|a", "a", True, split="dev")]
    with pytest.raises(ReviewTreatmentError, match="differ"):
        pilot.apply_review_treatments(items, {"P7_outside|a": _syn_t("P7_outside|a", "a", True, "keep")}, [])


def test_apply_treatments_synthetic_keep_and_exclude():
    items = [_syn("P1|x", "x", "", subset="P1"), _syn("P7_outside|a", "a", True), _syn("P7_outside|b", "b", False)]
    tre = {"P7_outside|a": _syn_t("P7_outside|a", "a", True, "exclude"),
           "P7_outside|b": _syn_t("P7_outside|b", "b", False, "keep")}
    log, audit = [], []
    out = pilot.apply_review_treatments(items, tre, log, audit)
    assert [r["item_id"] for r in out] == ["P1|x", "P7_outside|b"]
    assert [a["item_id"] for a in audit] == ["P7_outside|a"] and audit[0]["exclusion_reason"] == "r"
    assert len(log) == 1 and log[0][0] == "review_exclusion"


# ------------------------------------------------------------------------------- original records preserved
def test_original_review_records_unchanged():
    for name, sha in ORIGINAL_RECORDS.items():
        assert _sha(os.path.join(PILOT, name)) == sha, f"{name} was modified"


def test_scan_file_still_unreviewed_and_unread():
    """The scan file stays exactly as reviewed (REVIEWED: no) and no code path reads its status line."""
    text = open(os.path.join(PILOT, pilot.PLAIN_FILE), encoding="utf-8").read()
    assert text.endswith("REVIEWED: no\nEXCEPTIONS:\n")
    assert not hasattr(pilot, "plain_exceptions") and not hasattr(pilot, "lookalike_decisions")


# ----------------------------------------------------------------------------------- overwrite protection
def test_sheet_writers_never_overwrite(tmp_path):
    """Existing sheets are kept byte-for-byte, including undecided sheets and a scan file saying 'REVIEWED: no'."""
    pdir = str(tmp_path)
    contents = {
        pilot.PILOT_FILE: b"pilot_id\r\nP01\r\n",                                # no decisions at all
        pilot.LOOKALIKE_FILE: b"item_id,input_text\r\nP7_outside|x,x\r\n",        # undecided look-alike sheet
        pilot.PLAIN_FILE: open(os.path.join(PILOT, pilot.PLAIN_FILE), "rb").read(),  # REVIEWED: no
    }
    for name, data in contents.items():
        (tmp_path / name).write_bytes(data)
    pilot.build_pilot(config()["seed"], pilot_dir=pdir)
    pilot.build_lookalike_sheet(pilot_dir=pdir)
    pilot.build_plain_scan_sheet(pilot_dir=pdir)
    for name, data in contents.items():
        assert (tmp_path / name).read_bytes() == data, f"{name} was overwritten"


def test_sheet_writers_create_missing_sheets(tmp_path):
    pdir = str(tmp_path)
    pilot.build_pilot(config()["seed"], pilot_dir=pdir)
    pilot.build_lookalike_sheet(pilot_dir=pdir)
    pilot.build_plain_scan_sheet(pilot_dir=pdir)
    assert len(read_csv(str(tmp_path / pilot.PILOT_FILE))) == 10
    assert (tmp_path / pilot.PLAIN_FILE).read_text(encoding="utf-8").endswith("REVIEWED: no\nEXCEPTIONS:\n")


def test_sheet_writers_leave_real_pilot_dir_untouched(tmp_path, monkeypatch):
    """Default-path call (as `--stage pilot` would make) against a COPY of pilot/: nothing changes."""
    pdir = _pilot_copy(tmp_path / "pilot")
    before = {n: _sha(os.path.join(pdir, n)) for n in os.listdir(pdir) if os.path.isfile(os.path.join(pdir, n))}
    monkeypatch.setattr(pilot, "PILOT", pdir)
    pilot.build_pilot(config()["seed"])
    pilot.build_lookalike_sheet()
    pilot.build_plain_scan_sheet()
    after = {n: _sha(os.path.join(pdir, n)) for n in os.listdir(pdir) if os.path.isfile(os.path.join(pdir, n))}
    assert before == after


# ------------------------------------------------------------------------------------------- freeze guard
@pytest.fixture
def ready(built, tmp_path):
    """Temporary copies of a correctly built generated dir and pilot dir."""
    gen = tmp_path / "gen"
    shutil.copytree(built["gen"], gen)
    pdir = _pilot_copy(tmp_path / "pilot")
    return gen, pdir


def test_freeze_guard_accepts_authoritative_build(ready):
    gen, pdir = ready
    assert run_all.freeze_preconditions(str(gen), pdir) == []


def test_freeze_guard_does_not_use_scan_status_line(ready):
    gen, pdir = ready
    assert "REVIEWED: no" in open(os.path.join(pdir, pilot.PLAIN_FILE), encoding="utf-8").read()
    os.remove(os.path.join(pdir, pilot.PLAIN_FILE))
    assert run_all.freeze_preconditions(str(gen), pdir) == []


def _pre_rebuild_gen(dst):
    """A temporary copy of the PRE-REBUILD generated directory: the original product benchmark and build log from
    a0129b8, the (unchanged) country and malformed benchmarks, and no excluded_items.csv."""
    import subprocess
    from lexeval.paths import REPO
    dst.mkdir()
    (dst / "product_benchmark.csv").write_bytes(original_product_bytes())
    log = subprocess.run(["git", "-C", REPO, "show",
                          f"{ORIGINAL_COMMIT}:research_paper/experiments/data/generated/build_log.json"],
                         capture_output=True, check=True).stdout
    (dst / "build_log.json").write_bytes(log)
    for f in ("country_benchmark.csv", "malformed_inputs.csv"):
        shutil.copy(os.path.join(GEN, f), dst / f)
    return dst


def test_freeze_guard_refuses_current_pre_phase_d_draft(tmp_path):
    """Pre-rebuild state (reconstructed from the immutable original): refused, no excluded_items.csv.
    Live state (strict two-state check): refused before the rebuild; accepted after it."""
    pre = _pre_rebuild_gen(tmp_path / "pre")
    problems = run_all.freeze_preconditions(str(pre), _pilot_copy(tmp_path / "pilot"))
    assert problems and any("excluded_items.csv" in p for p in problems)
    state = assert_expected_live_state()
    live = run_all.freeze_preconditions()
    if state == "pre":
        assert live and any("excluded_items.csv" in p for p in live)
    else:
        assert live == [], live


def test_freeze_guard_refuses_draft_still_containing_exclusions(ready):
    gen, pdir = ready
    (gen / "product_benchmark.csv").write_bytes(original_product_bytes())   # original still has the 4 items
    problems = run_all.freeze_preconditions(str(gen), pdir)
    assert any("still present" in p for p in problems)


def test_freeze_guard_refuses_incomplete_audit_file(ready):
    gen, pdir = ready
    rows = csv_rows((gen / run_all.EXCLUDED_FILE).read_bytes())
    with open(gen / run_all.EXCLUDED_FILE, "w", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerows(rows[:-1])
    assert any("exactly the authorised exclusions" in p for p in run_all.freeze_preconditions(str(gen), pdir))


def test_freeze_guard_refuses_audit_reason_mismatch(ready):
    gen, pdir = ready
    rows = csv_rows((gen / run_all.EXCLUDED_FILE).read_bytes())
    i = rows[0].index("exclusion_reason")
    rows[1][i] = "edited"
    with open(gen / run_all.EXCLUDED_FILE, "w", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerows(rows)
    assert any("exclusion_reason" in p for p in run_all.freeze_preconditions(str(gen), pdir))


def test_freeze_guard_refuses_invalid_decisions_file(ready):
    gen, pdir = ready
    path = os.path.join(pdir, pilot.TREATMENTS_FILE)
    header, rows = _treatment_rows(path)
    _row(rows, "P7_outside|video game")["authorised_treatment"] = "keep"
    _write_treatments(path, header, rows)
    assert any("decisions file invalid" in p for p in run_all.freeze_preconditions(str(gen), pdir))


def test_freeze_guard_refuses_decisions_changed_after_build(ready):
    gen, pdir = ready
    path = os.path.join(pdir, pilot.TREATMENTS_FILE)
    header, rows = _treatment_rows(path)
    _row(rows, "P7_outside|sandwich")["reason"] += " (edited)"  # still valid, but not what the build used
    _write_treatments(path, header, rows)
    assert any("build_log.json does not record" in p for p in run_all.freeze_preconditions(str(gen), pdir))


def test_freeze_guard_refuses_review_record_changed_after_build(ready):
    gen, pdir = ready
    path = os.path.join(pdir, pilot.LOOKALIKE_FILE)  # temporary copy of the record
    rows = csv_rows(open(path, "rb").read())
    rows[1][6] = "comment added later"  # decisions unchanged, so the decisions file stays valid
    with open(path, "w", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerows(rows)
    assert any("build_log.json does not record" in p for p in run_all.freeze_preconditions(str(gen), pdir))


def test_freeze_guard_refuses_missing_log_entry(ready):
    gen, pdir = ready
    log = json.load(open(gen / "build_log.json", encoding="utf-8"))
    log = [e for e in log if not (e[0] == "review_exclusion" and e[1].startswith("P7_outside|toothbrush"))]
    json.dump(log, open(gen / "build_log.json", "w", encoding="utf-8"))
    assert any("review_exclusion" in p for p in run_all.freeze_preconditions(str(gen), pdir))


def test_stage_freeze_refuses_without_writing_manifest(ready, tmp_path, monkeypatch):
    gen, pdir = ready
    (gen / "product_benchmark.csv").write_bytes(original_product_bytes())  # invalid state: original draft
    manifest = gen / "MANIFEST.json"
    monkeypatch.setattr(run_all, "GEN", str(gen))
    monkeypatch.setattr(run_all, "PILOT", pdir)
    monkeypatch.setattr(run_all, "MANIFEST", str(manifest))
    with pytest.raises(SystemExit, match="Freeze refused"):
        run_all.stage_freeze("test")
    with pytest.raises(SystemExit, match="approved-by"):
        run_all.stage_freeze("")
    assert not manifest.exists()
    assert not os.path.exists(os.path.join(GEN, "MANIFEST.json"))
