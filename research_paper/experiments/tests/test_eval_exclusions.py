"""Phase B (IMPLEMENTATION_PLAN.md): TEST evaluation exclusions.

End-to-end evaluation tests run ONLY on SYNTHETIC benchmarks written to pytest temporary directories (the
eight real item IDs with synthetic sentinel texts). No system is run on any real TEST item; no result is
written outside temporary directories. Tests that touch the real files only read them.
"""
import copy
import csv
import hashlib
import json
import os

import pytest
from _runfix import make_paths

import run_all
from lexeval import build_countries, build_products, eval_exclusions, evaluate, figures
from lexeval.build_common import read_csv, write_csv
from lexeval.eval_exclusions import EvaluationExclusionError
from lexeval.paths import EXP, GEN, PILOT
from lexeval.run_control import AuthorisedTestRun, RunControlError, close_run, open_run
from lexeval.systems import primary_systems

AUTHORISED = {  # item_id -> (pilot_id, benchmark, category)
    "P2_format|Scanner|ws_punct": ("P01", "product", "P2_format"),
    "P3_typo|Graphics Card|typo|0": ("P02", "product", "P3_typo"),
    "P4_short|WiFi Adapter|head_noun": ("P03", "product", "P4_short"),
    "P6_ambiguous|word|computer": ("P05", "product", "P6_ambiguous"),
    "P7_outside|card index": ("P06", "product", "P7_outside"),
    "P8_hs|other_chapter|080122": ("P07", "product", "P8_hs_formal"),
    "CB|DZ|official_name": ("P09", "country", "J3_iso_name"),
    "CE|sint": ("P10", "country", "J6_ambiguous"),
}
DEV_PILOT = {"P5_confusable|Memory Card|typo_distinguishing_word": "P04", "CD|NZ|es": "P08"}
# SHA-256 of committed files that Phase B must not change (verified 26 Nov 2026). The product benchmark is
# checked separately (Phase D step 0): it must be the immutable original from a0129b8 or exactly the original
# minus the four authorised P7 rows, as fixed by tests/_original.EXPECTED_LIVE_STATE.
PROTECTED = {
    "data/generated/country_benchmark.csv": "1bf3f48940c27b4ba7fad332bc8e0bbc367df1381a251e6345a3a6609444c929",
    "data/generated/malformed_inputs.csv": "bb3af78811f382e8f1bcab7d622cfbe0737177a7a4644e8724b0258ef19655df",
    "pilot/pilot_reviewed_items.json": "ce958c65996b1b7312ca621a55aaddc5e6d956e2916507c6902480e7ba4b384e",
    "pilot/pilot_review_sheet_v4.csv": "ec8e11edff4fbec412d771822e85e7e2039a165110a1bd6549ee36fd4d00356c",
}


def _sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


# ------------------------------------------------------------------------------------------ real files (read only)
def test_real_exclusion_file_is_valid_against_committed_benchmark():
    spec, sha = eval_exclusions.load_exclusions()
    assert sha == _sha(eval_exclusions.EXCLUSIONS_FILE)
    got = {it["item_id"]: (it["pilot_id"], it["benchmark"], it["category"]) for it in spec["exclusions"]}
    assert got == AUTHORISED and len(spec["exclusions"]) == 8
    assert all(it["split"] == "test" and it["reason"].strip() for it in spec["exclusions"])
    assert {d["item_id"]: d["pilot_id"] for d in spec["dev_pilot_items_not_excluded"]} == DEV_PILOT
    assert spec["sensitivity_sibling_clusters"]["product"] == sorted(
        ["base:Scanner", "base:Graphics Card", "base:WiFi Adapter", "P6_ambiguous|word|computer",
         "P7_outside|card index", "P8_hs|other_chapter|080122"])
    assert spec["sensitivity_sibling_clusters"]["country"] == ["CE|sint", "DZ"]


def test_real_exclusions_are_test_items_and_dev_pilot_items_are_dev():
    rows = {n: {r["item_id"]: r for r in read_csv(os.path.join(GEN, f))}
            for n, f in eval_exclusions.BENCHMARK_FILES.items()}
    for iid, (_, bench, cat) in AUTHORISED.items():
        assert rows[bench][iid]["split"] == "test" and rows[bench][iid]["subset"] == cat
    assert rows["product"]["P5_confusable|Memory Card|typo_distinguishing_word"]["split"] == "dev"
    assert rows["country"]["CD|NZ|es"]["split"] == "dev"


def test_real_choke_point_removes_exactly_eight_and_nothing_else():
    """Counts only: TEST rows are loaded through the choke point; no system is run and nothing is scored."""
    sha = eval_exclusions.exclusions_sha256()
    ts = eval_exclusions.load_test_items(sha)
    for name, scored, n_ex in (("product", ts.product, 6), ("country", ts.country, 2)):
        test = [r for r in read_csv(os.path.join(GEN, eval_exclusions.BENCHMARK_FILES[name])) if r["split"] == "test"]
        assert len(scored) == len(test) - n_ex
        assert {r["item_id"] for r in test} - {r["item_id"] for r in scored} == \
            {i for i, v in AUTHORISED.items() if v[1] == name}
        assert all(r["split"] == "test" for r in scored)
    assert sorted(e["item_id"] for e in ts.excluded) == sorted(AUTHORISED)
    assert all(e["reason"] and e["exclusions_sha256"] == sha for e in ts.excluded)


def test_protected_files_unchanged():
    from _original import ORIGINAL_SHA256, assert_expected_live_state, expected_rebuilt_bytes, original_product_bytes
    for rel, sha in PROTECTED.items():
        assert _sha(os.path.join(EXP, rel)) == sha, f"{rel} was modified"
    assert hashlib.sha256(original_product_bytes()).hexdigest() == ORIGINAL_SHA256
    state = assert_expected_live_state()
    live = open(os.path.join(EXP, "data/generated/product_benchmark.csv"), "rb").read()
    assert live == (original_product_bytes() if state == "pre" else expected_rebuilt_bytes())


def test_validation_report_includes_exclusions():
    from lexeval.validate import validate
    rep = validate()
    assert not [e for e in rep["errors"] if "exclusion" in e]
    st = rep["stats"]["evaluation_exclusions"]
    assert st["n_excluded"] == 8 and st["by_benchmark"] == {"product": 6, "country": 2}
    assert st["sha256"] == eval_exclusions.exclusions_sha256()


# -------------------------------------------------------------------------------------------- synthetic fixture
def _prod(iid, subset, text, expected, label_hs, cluster, split, look_alike=""):
    return dict(item_id=iid, subset=subset, text=text, expected=expected, label_hs=label_hs, label_base_types="",
                abstain_reason="" if expected == "ANSWER" else "synthetic", label_source="synthetic",
                mapping_basis="synthetic", hs_exists="", in_catalogue_support="", transform="none",
                look_alike=look_alike, parent="", group=cluster, cluster=cluster, split=split)


def _ctry(iid, subset, text, iso, avail, action, builtin, cluster, split):
    return dict(item_id=iid, subset=subset, text=text, gold_iso=iso, label_kind="country" if iso else "none",
                tax_data_available=avail, gold_tax_action=action, form="synthetic", s1_builtin=builtin,
                label_source="synthetic", transform="none", group=cluster, cluster=cluster, split=split)


SYN_PRODUCT = [
    # the six excluded product items (sentinel texts; split test)
    _prod("P2_format|Scanner|ws_punct", "P2_format", "SENTINEL-P01", "ANSWER", "847160", "base:Scanner", "test"),
    _prod("P3_typo|Graphics Card|typo|0", "P3_typo", "SENTINEL-P02", "ANSWER", "847180", "base:Graphics Card", "test"),
    _prod("P4_short|WiFi Adapter|head_noun", "P4_short", "SENTINEL-P03", "ABSTAIN", "", "base:WiFi Adapter", "test"),
    _prod("P6_ambiguous|word|computer", "P6_ambiguous", "SENTINEL-P05", "ABSTAIN", "", "P6_ambiguous|word|computer", "test"),
    _prod("P7_outside|card index", "P7_outside", "SENTINEL-P06", "ABSTAIN", "", "P7_outside|card index", "test", "True"),
    _prod("P8_hs|other_chapter|080122", "P8_hs_formal", "SENTINEL-P07", "ABSTAIN", "", "P8_hs|other_chapter|080122", "test"),
    # siblings (same clusters, TEST)
    _prod("P1_exact|Scanner|base_name", "P1_exact", "Scanner", "ANSWER", "847160", "base:Scanner", "test"),
    _prod("P1_exact|Graphics Card|base_name", "P1_exact", "Graphics Card", "ANSWER", "847180", "base:Graphics Card", "test"),
    _prod("P2_format|WiFi Adapter|case", "P2_format", "wifi adapter", "ANSWER", "851762", "base:WiFi Adapter", "test"),
    # other TEST items
    _prod("P1_exact|Laptop|base_name", "P1_exact", "Laptop", "ANSWER", "847130", "base:Laptop", "test"),
    _prod("P2_format|Laptop|case", "P2_format", "LAPTOP", "ANSWER", "847130", "base:Laptop", "test"),
    _prod("P7_outside|sandwich", "P7_outside", "sandwich", "ABSTAIN", "", "P7_outside|sandwich", "test", "False"),
    _prod("P8_hs|other_chapter|010121", "P8_hs_formal", "Horses; live, pure-bred", "ABSTAIN", "",
          "P8_hs|other_chapter|010121", "test"),
    # DEV items, including the DEV pilot item P04
    _prod("P5_confusable|Memory Card|typo_distinguishing_word", "P5_confusable", "SENTINEL-P04", "ANSWER", "852351",
          "base:Memory Card", "dev"),
    _prod("P1_exact|Memory Card|base_name", "P1_exact", "Memory Card", "ANSWER", "852351", "base:Memory Card", "dev"),
]
SYN_COUNTRY = [
    _ctry("CB|DZ|official_name", "J3_iso_name", "SENTINEL-P09", "DZ", "False", "REFUSE", "True", "DZ", "test"),
    _ctry("CE|sint", "J6_ambiguous", "SENTINEL-P10", "", "False", "REFUSE", "False", "CE|sint", "test"),
    _ctry("CA|DZ|alpha2", "J2_iso_code", "DZ", "DZ", "False", "REFUSE", "True", "DZ", "test"),           # sibling
    _ctry("CA|DE|table", "J1_table", "Germany", "DE", "True", "COMPUTE", "True", "DE", "test"),
    _ctry("CC|DE|typo", "J4_typo", "Germnay", "DE", "True", "COMPUTE", "False", "DE", "test"),
    _ctry("CE|georgia", "J6_ambiguous", "Georgia", "", "False", "REFUSE", "False", "CE|georgia", "test"),
    _ctry("CD|NZ|es", "J5_cldr", "SENTINEL-P08", "NZ", "False", "REFUSE", "False", "NZ", "dev"),
]
SENTINELS = [r["text"] for r in SYN_PRODUCT + SYN_COUNTRY if r["text"].startswith("SENTINEL")]
SIBLINGS = {"P1_exact|Scanner|base_name", "P1_exact|Graphics Card|base_name", "P2_format|WiFi Adapter|case",
            "CA|DZ|alpha2"}


def _write_pilot(pdir):
    os.makedirs(pdir, exist_ok=True)
    rec = json.load(open(os.path.join(PILOT, "pilot_reviewed_items.json"), encoding="utf-8"))
    text = {r["item_id"]: r["text"] for r in SYN_PRODUCT + SYN_COUNTRY}
    with open(os.path.join(pdir, "pilot_reviewed_items.json"), "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=2)
    with open(os.path.join(pdir, "pilot_review_sheet_v4.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["pilot_id", "input_text", "reviewer_decision(Accept/Reject/Uncertain)"])
        for it in rec["items"]:
            w.writerow([it["pilot_id"], text[it["item_id"]], it["decision"]])


def _spec(exp):
    rec = json.load(open(os.path.join(exp, "pilot", "pilot_reviewed_items.json"), encoding="utf-8"))
    rows = {r["item_id"]: r for r in SYN_PRODUCT + SYN_COUNTRY}
    items, dev = [], []
    for it in rec["items"]:
        r = rows[it["item_id"]]
        if it["split"] != "test":
            dev.append({"pilot_id": it["pilot_id"], "item_id": it["item_id"], "benchmark": it["benchmark"],
                        "split": "dev", "treatment": "not excluded"})
            continue
        items.append({"pilot_id": it["pilot_id"], "item_id": it["item_id"], "benchmark": it["benchmark"],
                      "split": "test", "category": r["subset"], "text": r["text"], "cluster": r["cluster"],
                      "pilot_decision": it["decision"], "reason": "inspected during pilot (synthetic)",
                      "source_record": "pilot/pilot_reviewed_items.json"})
    return {"schema": eval_exclusions.SCHEMA, "purpose": "synthetic", "authorisation": {},
            "source_records": {r: _sha(os.path.join(exp, r)) for r in
                               ("pilot/pilot_reviewed_items.json", "pilot/pilot_review_sheet_v4.csv")},
            "exclusions": items, "dev_pilot_items_not_excluded": dev,
            "sensitivity_sibling_clusters": {
                "definition": "synthetic",
                "product": sorted({i["cluster"] for i in items if i["benchmark"] == "product"}),
                "country": sorted({i["cluster"] for i in items if i["benchmark"] == "country"})}}


@pytest.fixture
def syn(tmp_path):
    exp = tmp_path / "exp"
    gen, pdir = exp / "gen", exp / "pilot"
    _write_pilot(str(pdir))
    write_csv(str(gen / "product_benchmark.csv"), SYN_PRODUCT, build_products.FIELDS)
    write_csv(str(gen / "country_benchmark.csv"), SYN_COUNTRY, build_countries.FIELDS)
    spec = _spec(str(exp))
    path = exp / "evaluation_exclusions_v1.json"
    path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    return {"exp": exp, "gen": str(gen), "pilot": str(pdir), "path": str(path), "spec": spec,
            "sha": _sha(str(path))}


def _bench(s):
    return {"product": read_csv(os.path.join(s["gen"], "product_benchmark.csv")),
            "country": read_csv(os.path.join(s["gen"], "country_benchmark.csv"))}


def _errs(s, mutate=None, bench_mutate=None):
    spec = copy.deepcopy(s["spec"])
    if mutate:
        mutate(spec)
    bench = _bench(s)
    if bench_mutate:
        bench_mutate(bench)
    return eval_exclusions.validate_exclusions(spec, s["pilot"], bench)


def _item(spec, iid):
    return next(i for i in spec["exclusions"] if i["item_id"] == iid)


# ------------------------------------------------------------------------------------------ validation failures
def test_synthetic_spec_valid(syn):
    assert _errs(syn) == []


def test_missing_id_rejected(syn):
    def m(spec):
        spec["exclusions"] = [i for i in spec["exclusions"] if i["item_id"] != "CE|sint"]
    errs = _errs(syn, m)
    assert any("CE|sint" in e and "missing" in e for e in errs)


def test_duplicate_id_rejected(syn):
    errs = _errs(syn, lambda spec: spec["exclusions"].append(dict(spec["exclusions"][0])))
    assert any("duplicate" in e for e in errs)


def test_unknown_id_rejected(syn):
    def m(spec):
        _item(spec, "P7_outside|card index")["item_id"] = "P7_outside|filing cabinet"
    errs = _errs(syn, m)
    assert any("filing cabinet" in e and "unknown" in e for e in errs)
    assert any("card index" in e and "missing" in e for e in errs)


def test_dev_item_cannot_be_excluded(syn):
    rows = {r["item_id"]: r for r in SYN_PRODUCT}

    def m(spec):  # P04 is a DEV pilot item; listed with its true split
        r = rows["P5_confusable|Memory Card|typo_distinguishing_word"]
        spec["exclusions"].append({"pilot_id": "P04", "item_id": r["item_id"], "benchmark": "product",
                                   "split": "dev", "category": r["subset"], "text": r["text"],
                                   "cluster": r["cluster"], "pilot_decision": "Accept", "reason": "x",
                                   "source_record": "pilot/pilot_reviewed_items.json"})
    errs = _errs(syn, m)
    assert any("Memory Card" in e and "only TEST" in e for e in errs)
    assert any("Memory Card" in e and "must not be excluded" in e for e in errs)


def test_dev_item_claimed_as_test_rejected(syn):
    rows = {r["item_id"]: r for r in SYN_COUNTRY}

    def m(spec):
        r = rows["CD|NZ|es"]
        spec["exclusions"].append({"pilot_id": "P08", "item_id": r["item_id"], "benchmark": "country",
                                   "split": "test", "category": r["subset"], "text": r["text"],
                                   "cluster": r["cluster"], "pilot_decision": "Accept", "reason": "x",
                                   "source_record": "pilot/pilot_reviewed_items.json"})
    errs = _errs(syn, m)
    assert any("CD|NZ|es" in e and "contradict the pilot record" in e for e in errs)
    assert any("CD|NZ|es" in e and "not 'test'" in e for e in errs)


def test_benchmark_split_must_be_test(syn):
    def b(bench):
        next(r for r in bench["country"] if r["item_id"] == "CE|sint")["split"] = "dev"
    assert any("CE|sint" in e and "not 'test'" in e for e in _errs(syn, bench_mutate=b))


@pytest.mark.parametrize("field,value,needle", [
    ("split", "dev", "contradict the pilot record"),
    ("benchmark", "country", "contradict the pilot record"),
    ("pilot_id", "P02", "contradict the pilot record"),
    ("pilot_decision", "Reject", "contradict the pilot record"),
    ("category", "P3_typo", "category"),
    ("text", "Scanner", "pilot review sheet"),
    ("cluster", "base:Laptop", "cluster"),
    ("reason", " ", "non-empty reason"),
    ("source_record", "pilot/other.json", "source_record"),
])
def test_inconsistent_entry_rejected(syn, field, value, needle):
    def m(spec):
        _item(spec, "P2_format|Scanner|ws_punct")[field] = value
    errs = _errs(syn, m)
    assert any("Scanner|ws_punct" in e and needle in e for e in errs), errs


def test_pilot_record_contradiction_rejected(syn):
    """If the pilot record itself says something else, the exclusion file no longer matches it."""
    p = os.path.join(syn["pilot"], "pilot_reviewed_items.json")
    rec = json.load(open(p, encoding="utf-8"))
    rec["items"][0]["decision"] = "Reject"
    json.dump(rec, open(p, "w", encoding="utf-8"), indent=2)
    assert any("source record changed" in e for e in _errs(syn))
    # with refreshed provenance hashes the content contradiction is still caught
    def m(spec):
        spec["source_records"]["pilot/pilot_reviewed_items.json"] = _sha(p)
    assert any("Scanner|ws_punct" in e and "contradict the pilot record" in e for e in _errs(syn, m))


def test_id_missing_from_or_duplicated_in_benchmark_rejected(syn):
    def drop(bench):
        bench["product"] = [r for r in bench["product"] if r["item_id"] != "P7_outside|card index"]
    assert any("card index" in e and "found 0" in e for e in _errs(syn, bench_mutate=drop))

    def dup(bench):
        bench["country"].append(dict(next(r for r in bench["country"] if r["item_id"] == "CE|sint")))
    assert any("CE|sint" in e and "found 2" in e for e in _errs(syn, bench_mutate=dup))


def test_wrong_sibling_clusters_and_schema_rejected(syn):
    def m(spec):
        spec["sensitivity_sibling_clusters"]["country"] = ["DZ"]
    assert any("sensitivity_sibling_clusters[country]" in e for e in _errs(syn, m))
    assert _errs(syn, lambda spec: spec.update(schema="other")) == [f"schema must be {eval_exclusions.SCHEMA!r}"]


def test_malformed_file_stops_guard(tmp_path):
    p = tmp_path / "x.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(EvaluationExclusionError):
        eval_exclusions.excluded_ids(str(p))
    p.write_text(json.dumps({"schema": eval_exclusions.SCHEMA, "exclusions": []}), encoding="utf-8")
    with pytest.raises(EvaluationExclusionError):
        eval_exclusions.excluded_ids(str(p))


# ----------------------------------------------------------------------------------------- hash and choke point
def test_hash_generation(syn):
    sha = eval_exclusions.exclusions_sha256(syn["path"])
    assert sha == hashlib.sha256(open(syn["path"], "rb").read()).hexdigest() == syn["sha"]
    with open(syn["path"], "a", encoding="utf-8") as fh:
        fh.write("\n")
    assert eval_exclusions.exclusions_sha256(syn["path"]) != sha


@pytest.mark.parametrize("sha", [None, "", "0" * 64])
def test_choke_point_requires_matching_manifest_hash(syn, sha):
    with pytest.raises(EvaluationExclusionError):
        eval_exclusions.load_test_items(sha, gen_dir=syn["gen"], path=syn["path"], pilot_dir=syn["pilot"])


def test_choke_point_counts_and_audit(syn):
    ts = eval_exclusions.load_test_items(syn["sha"], gen_dir=syn["gen"], path=syn["path"], pilot_dir=syn["pilot"])
    assert len(ts.product) == 7 and len(ts.country) == 4   # 13 - 6 and 6 - 2 TEST rows
    assert not {r["item_id"] for r in ts.product + ts.country} & set(AUTHORISED)
    assert all(r["split"] == "test" for r in ts.product + ts.country)       # no DEV item
    assert sorted(e["item_id"] for e in ts.excluded) == sorted(AUTHORISED)
    assert {e["item_id"]: e["category"] for e in ts.excluded} == {k: v[2] for k, v in AUTHORISED.items()}


def test_choke_point_stops_on_invalid_file(syn):
    spec = copy.deepcopy(syn["spec"])
    spec["exclusions"].pop()
    with open(syn["path"], "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with pytest.raises(EvaluationExclusionError, match="missing"):
        eval_exclusions.load_test_items(eval_exclusions.exclusions_sha256(syn["path"]), gen_dir=syn["gen"],
                                        path=syn["path"], pilot_dir=syn["pilot"])


# ------------------------------------------------------------------------- end-to-end on the synthetic benchmark
@pytest.fixture
def evaluated(syn, tmp_path, monkeypatch):
    # Phase C: TEST evaluation runs only inside an authorised run opened from a verified (synthetic) manifest.
    monkeypatch.setattr(evaluate, "RESULTS", str(tmp_path / "unused_results"))
    paths = make_paths(tmp_path, syn["gen"], syn["path"], syn["pilot"])
    run = open_run(paths, "synthetic test")
    prows, crows, _ = evaluate.evaluate(primary_systems(), "test", "primary", run=run)
    close_run(run)
    from pathlib import Path
    return {"res": Path(run.run_dir), "prows": prows, "crows": crows, "run": run, **syn}


def _all_outputs(res):
    for root, _, files in os.walk(res):
        for f in files:
            yield os.path.join(root, f)


def test_no_excluded_item_reaches_any_output(evaluated):
    """Every raw and processed TEST output (items, propagation, summaries, paired tests, sensitivity):
    no excluded ID, sentinel text or excluded-only cluster appears; only the audit file lists them."""
    # The audit file lists the excluded items; the sensitivity info file lists the pre-declared cluster NAMES
    # (for singleton clusters a name equals an item ID). Neither holds metric values; both are checked below.
    metadata = {"primary_test_excluded_from_metrics.csv", "primary_test_sensitivity_siblings_info.json"}
    # Phase C run records (no item IDs): run.json, output hashes and the provenance file are leak-checked too.
    info = json.load(open(evaluated["res"] / "processed" / "primary_test_sensitivity_siblings_info.json"))
    assert set(info) == {"definition", "exclusions_sha256", "product_clusters", "country_clusters",
                         "product_sibling_items_removed", "country_sibling_items_removed"}
    checked = set()
    for path in _all_outputs(evaluated["res"]):
        if os.path.basename(path) in metadata:
            continue
        text = open(path, encoding="utf-8").read()
        for needle in list(AUTHORISED) + SENTINELS:
            assert needle not in text, f"{needle!r} leaked into {os.path.relpath(path, evaluated['res'])}"
        checked.add(os.path.basename(path))
    sens = "primary_sensitivity_siblings_removed_test"
    assert checked == {"run.json", "outputs_sha256.json", "close.json", "primary_test_provenance.json",
                       "primary_test_outputs.jsonl", "primary_test_product_items.csv", "primary_test_country_items.csv",
                       "primary_test_malformed_items.csv", "primary_test_product_summary.csv",
                       "primary_test_identification_summary.csv", "primary_test_tax_behaviour_summary.csv",
                       "primary_test_paired_tests.csv", f"{sens}_product_summary.csv",
                       f"{sens}_identification_summary.csv", f"{sens}_tax_behaviour_summary.csv",
                       f"{sens}_paired_tests.csv"}


def test_item_level_outputs_have_exact_scored_sets(evaluated):
    scored_p = {r["item_id"] for r in SYN_PRODUCT if r["split"] == "test"} - set(AUTHORISED)
    scored_c = {r["item_id"] for r in SYN_COUNTRY if r["split"] == "test"} - set(AUTHORISED)
    for name, scored in (("product", scored_p), ("country", scored_c)):
        rows = read_csv(str(evaluated["res"] / "processed" / f"primary_test_{name}_items.csv"))
        assert len(rows) == len(scored) * 3
        for s in ("B", "S0", "S1"):
            assert {r["item_id"] for r in rows if r["system"] == s} == scored
        assert all(r["propagation"] for r in rows)   # error-propagation classes computed on scored rows only


def test_summaries_and_paired_tests_count_only_scored_items(evaluated):
    proc = evaluated["res"] / "processed"
    summ = read_csv(str(proc / "primary_test_product_summary.csv"))
    expect = {"P1_exact": 3, "P2_format": 2, "P7_outside": 1, "P8_hs_formal": 1, "ALL": 6}  # ALL excludes P8
    for r in summ:
        assert int(r["n"]) == expect[r["subset"]], r
    assert not {r["subset"] for r in summ} & {"P3_typo", "P4_short", "P6_ambiguous"}  # only excluded items there
    ident = read_csv(str(proc / "primary_test_identification_summary.csv"))
    assert {r["subset"]: int(r["n"]) for r in ident if r["system"] == "B"} == \
        {"J1_table": 1, "J2_iso_code": 1, "J4_typo": 1, "J6_ambiguous": 1, "ALL": 2}  # ALL = held-out forms
    tests = read_csv(str(proc / "primary_test_paired_tests.csv"))
    assert len(tests) == 18
    n = {t["task"]: int(t["n_items"]) for t in tests}
    assert n == {"product": 6, "identification": 2, "tax_behaviour": 2}
    audit = read_csv(str(proc / "primary_test_excluded_from_metrics.csv"))
    assert sorted(r["item_id"] for r in audit) == sorted(AUTHORISED)
    assert all(r["reason"] and r["exclusions_sha256"] == evaluated["sha"] for r in audit)


def test_sensitivity_outputs_also_drop_sibling_clusters(evaluated):
    proc = evaluated["res"] / "processed"
    info = json.load(open(proc / "primary_test_sensitivity_siblings_info.json", encoding="utf-8"))
    assert (info["product_sibling_items_removed"], info["country_sibling_items_removed"]) == (3, 1)
    for name in ("product_summary", "identification_summary", "tax_behaviour_summary", "paired_tests"):
        path = proc / f"primary_sensitivity_siblings_removed_test_{name}.csv"
        assert path.exists()
    summ = read_csv(str(proc / "primary_sensitivity_siblings_removed_test_product_summary.csv"))
    assert {r["subset"]: int(r["n"]) for r in summ if r["system"] == "S1"} == \
        {"P1_exact": 1, "P2_format": 1, "P7_outside": 1, "P8_hs_formal": 1, "ALL": 3}
    primary = read_csv(str(proc / "primary_test_product_summary.csv"))
    assert {r["subset"]: int(r["n"]) for r in primary if r["system"] == "S1"}["ALL"] == 6  # primary unchanged


def test_figures_are_generated_from_guarded_summaries(evaluated, tmp_path, monkeypatch):
    monkeypatch.setattr(figures, "FIGURES", str(tmp_path))
    summ = str(evaluated["res"] / "processed" / "primary_test_product_summary.csv")
    figures.outcome_bars(summ, str(tmp_path / "f.pdf"), ["ALL", "P1_exact"], "synthetic")
    assert (tmp_path / "f.pdf").stat().st_size > 0


def test_every_metric_function_rejects_excluded_rows():
    """Independent guard: rows carrying an excluded ID cannot be summarised or tested, whatever path they took."""
    row = dict(item_id="CE|sint", system="B", subset="J6_ambiguous", cluster="CE|sint", outcome="CORRECT",
               identification="CORRECT", tax_behaviour="CORRECT", s1_builtin="False")
    ok = dict(row, item_id="CA|DE|table", cluster="DE")
    with pytest.raises(EvaluationExclusionError):
        evaluate.summarise_by([ok, row], "outcome")
    with pytest.raises(EvaluationExclusionError):
        evaluate.paired_tests([ok, row, dict(row, system="S1"), dict(ok, system="S1")], "outcome", [("B", "S1")], "x")
    with pytest.raises(EvaluationExclusionError):
        eval_exclusions.assert_no_excluded([row], "any")
    eval_exclusions.assert_no_excluded([ok], "any")


def test_evaluate_test_refuses_without_authorised_run_and_writes_nothing(syn, tmp_path, monkeypatch):
    """Phase C replaces the caller-supplied hash: TEST needs an open run whose manifest verifies."""
    res = tmp_path / "evaluate_results"  # distinct from make_paths' results dir
    monkeypatch.setattr(evaluate, "RESULTS", str(res))
    with pytest.raises(RunControlError):
        evaluate.evaluate(primary_systems(), "test", "primary")
    forged = AuthorisedTestRun("forged", str(tmp_path / "forged"), None,
                               {"evaluation_exclusions_sha256": syn["sha"]}, {})
    with pytest.raises(RunControlError):
        evaluate.evaluate(primary_systems(), "test", "primary", run=forged)
    # a manifest recording a different exclusion hash cannot be opened
    paths = make_paths(tmp_path, syn["gen"], syn["path"], syn["pilot"])
    man = json.load(open(paths.manifest))
    man["evaluation_exclusions_sha256"] = "f" * 64
    json.dump(man, open(paths.manifest, "w"))
    with pytest.raises(RunControlError, match="evaluation_exclusions"):
        open_run(paths, "synthetic test")
    assert not res.exists() and not os.path.exists(paths.runs)


def test_unknown_split_refused():
    with pytest.raises(ValueError):
        evaluate.load("train")


def test_dev_evaluation_unaffected(syn, tmp_path, monkeypatch):
    monkeypatch.setattr(evaluate, "RESULTS", str(tmp_path / "r"))
    prows, crows, _ = evaluate.evaluate(primary_systems(), "dev", "devcheck", gen_dir=syn["gen"])
    assert {r["item_id"] for r in prows} == {r["item_id"] for r in SYN_PRODUCT if r["split"] == "dev"}
    assert {r["item_id"] for r in crows} == {"CD|NZ|es"}


def test_benchmark_rows_unchanged_by_evaluation(evaluated):
    """Evaluation-time exclusion only: the (synthetic) benchmark files keep every row and label."""
    for name, rows in (("product_benchmark.csv", SYN_PRODUCT), ("country_benchmark.csv", SYN_COUNTRY)):
        got = read_csv(os.path.join(evaluated["gen"], name))
        assert [r["item_id"] for r in got] == [r["item_id"] for r in rows]
        assert all(g == {k: str(v) for k, v in r.items()} for g, r in zip(got, rows))


# ---------------------------------------------------------------------------------------- freeze / evaluate stage
def test_stage_evaluate_refuses_manifest_without_exclusions_hash(syn, tmp_path):
    paths = make_paths(tmp_path, syn["gen"], syn["path"], syn["pilot"], omit="evaluation_exclusions_sha256")
    with pytest.raises(SystemExit, match="evaluation_exclusions_sha256"):
        run_all.stage_evaluate({}, "test", "synthetic test", paths=paths)
    assert not os.path.exists(paths.runs) and not os.path.exists(paths.log)


def test_freeze_guard_checks_exclusions_before_build_state(tmp_path):
    """With a valid decisions file, an invalid exclusion file is reported before any build-state check."""
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"schema": "wrong"}), encoding="utf-8")
    problems = run_all.freeze_preconditions(exclusions_path=str(bad))
    assert len(problems) == 1 and problems[0].startswith("evaluation exclusions invalid")
