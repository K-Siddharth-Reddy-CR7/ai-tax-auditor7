"""Phase B (IMPLEMENTATION_PLAN.md): the single choke point for TEST evaluation exclusions.

`evaluation_exclusions_v1.json` lists the TEST items inspected during the labelling-rule pilot. They are
removed from EVERY TEST metric; their benchmark rows, labels and splits are never changed.

Design
- `load_exclusions()` reads the file and validates it against the pilot records and the benchmark. Any
  problem raises EvaluationExclusionError, so evaluation stops instead of continuing silently.
- `load_test_items()` is the ONLY function that returns TEST benchmark rows for scoring. It requires the
  exclusion file's SHA-256 recorded in the freeze manifest, validates, removes the excluded IDs, and returns
  the scored rows together with an audit list of the removed rows.
- `assert_no_excluded()` is a second, independent guard. It is called by every metric function in
  evaluate.py (summaries, paired tests, sensitivity) and by the writer of item-level outputs. A row with an
  excluded ID raises, whatever path it came from.
- `without_sibling_clusters()` derives the secondary sensitivity set (clusters fixed in the file).
"""
import csv
import hashlib
import json
import os
from collections import Counter

from .build_common import read_csv
from .paths import EXP, GEN, PILOT

EXCLUSIONS_FILE = os.path.join(EXP, "evaluation_exclusions_v1.json")
SCHEMA = "lexitax-evaluation-exclusions/1"
BENCHMARK_FILES = {"product": "product_benchmark.csv", "country": "country_benchmark.csv"}
PILOT_RECORD = "pilot/pilot_reviewed_items.json"
PILOT_SHEET = "pilot/pilot_review_sheet_v4.csv"
ITEM_KEYS = ["pilot_id", "item_id", "benchmark", "split", "category", "text", "cluster", "pilot_decision",
             "reason", "source_record"]
AUDIT_FIELDS = ["benchmark", "pilot_id", "item_id", "split", "category", "cluster", "text", "reason",
                "source_record", "exclusions_sha256"]


class EvaluationExclusionError(ValueError):
    """The exclusion file is invalid, inconsistent, or does not match the frozen manifest."""


def exclusions_sha256(path=None):
    with open(path or EXCLUSIONS_FILE, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        raise EvaluationExclusionError(f"exclusion file not found: {path}") from None
    except json.JSONDecodeError as e:
        raise EvaluationExclusionError(f"exclusion file is not valid JSON: {path}: {e}") from None


def validate_exclusions(spec, pilot_dir, benchmarks):
    """Return a list of problems (empty = valid).

    spec        parsed exclusion file
    pilot_dir   directory holding pilot_reviewed_items.json and pilot_review_sheet_v4.csv
    benchmarks  {"product": [rows], "country": [rows]} as read from the benchmark CSVs
    """
    errs = []
    if spec.get("schema") != SCHEMA:
        return [f"schema must be {SCHEMA!r}"]
    items = spec.get("exclusions")
    if not isinstance(items, list) or not items:
        return ["'exclusions' must be a non-empty list"]
    exp_root = os.path.dirname(os.path.abspath(pilot_dir))
    # provenance: the pilot records must be exactly the files the exclusion list was derived from
    for rel, want in (spec.get("source_records") or {}).items():
        p = os.path.join(exp_root, rel)
        if not os.path.exists(p):
            errs.append(f"source record missing: {rel}")
        elif _sha(p) != want:
            errs.append(f"source record changed since the exclusion file was written: {rel}")
    if set(spec.get("source_records") or {}) != {PILOT_RECORD, PILOT_SHEET}:
        errs.append(f"source_records must list exactly {PILOT_RECORD} and {PILOT_SHEET}")
    if errs:
        return errs
    pilot = json.load(open(os.path.join(exp_root, PILOT_RECORD), encoding="utf-8"))["items"]
    sheet = {r["pilot_id"]: r for r in read_csv(os.path.join(exp_root, PILOT_SHEET))}
    by_pilot_item = {p["item_id"]: p for p in pilot}
    index = {}
    for name, rows in benchmarks.items():
        for r in rows:
            index.setdefault(r["item_id"], []).append((name, r))

    counts = Counter(it.get("item_id") for it in items)
    for iid, n in sorted(counts.items(), key=lambda kv: str(kv[0])):
        if n > 1:
            errs.append(f"{iid}: listed {n} times (duplicate exclusion)")
    pilot_test = {p["item_id"] for p in pilot if p["split"] == "test"}
    for iid in sorted(pilot_test - set(counts)):
        errs.append(f"{iid}: pilot-reviewed TEST item missing from the exclusion file")
    for it in items:
        if sorted(it) != sorted(ITEM_KEYS):
            errs.append(f"{it.get('item_id')}: entry must have exactly the keys {ITEM_KEYS}")
            continue
        iid = it["item_id"]
        p = by_pilot_item.get(iid)
        if p is None:
            errs.append(f"{iid}: not an item in the pilot record (unknown ID)")
            continue
        if (it["pilot_id"], it["benchmark"], it["split"], it["pilot_decision"]) != \
                (p["pilot_id"], p["benchmark"], p["split"], p["decision"]):
            errs.append(f"{iid}: pilot_id/benchmark/split/decision contradict the pilot record "
                        f"({p['pilot_id']}, {p['benchmark']}, {p['split']}, {p['decision']})")
        if it["split"] != "test" or p["split"] != "test":
            errs.append(f"{iid}: only TEST items may be excluded (a DEV item never enters TEST metrics)")
        s = sheet.get(it["pilot_id"])
        if s is None or s["input_text"] != it["text"]:
            errs.append(f"{iid}: text does not match the pilot review sheet")
        if it["source_record"] != PILOT_RECORD or not str(it["reason"]).strip():
            errs.append(f"{iid}: needs source_record {PILOT_RECORD!r} and a non-empty reason")
        hits = index.get(iid, [])
        if len(hits) != 1:
            errs.append(f"{iid}: must occur exactly once across the benchmarks, found {len(hits)}")
            continue
        name, r = hits[0]
        if name != it["benchmark"]:
            errs.append(f"{iid}: listed as {it['benchmark']} but found in the {name} benchmark")
        if r["split"] != "test":
            errs.append(f"{iid}: benchmark split is {r['split']!r}, not 'test' (DEV items cannot be excluded)")
        for key, col in (("category", "subset"), ("text", "text"), ("cluster", "cluster")):
            if it[key] != r[col]:
                errs.append(f"{iid}: {key} {it[key]!r} differs from the benchmark ({r[col]!r})")
    for d in spec.get("dev_pilot_items_not_excluded", []):
        if d.get("item_id") in counts:
            errs.append(f"{d.get('item_id')}: DEV pilot item must not be excluded")
    sib = spec.get("sensitivity_sibling_clusters") or {}
    for name in BENCHMARK_FILES:
        want = sorted({it["cluster"] for it in items if it.get("benchmark") == name and "cluster" in it})
        if sorted(sib.get(name, [])) != want:
            errs.append(f"sensitivity_sibling_clusters[{name}] must equal the clusters of its excluded items {want}")
    if not str(sib.get("definition", "")).strip():
        errs.append("sensitivity_sibling_clusters.definition is empty")
    return errs


def _read_benchmarks(gen_dir):
    return {name: read_csv(os.path.join(gen_dir, f)) for name, f in BENCHMARK_FILES.items()}


def load_exclusions(path=None, gen_dir=None, pilot_dir=None, benchmarks=None):
    """Validated exclusion spec plus its SHA-256. Raises EvaluationExclusionError on any problem."""
    path = path or EXCLUSIONS_FILE
    spec = _read_json(path)
    benchmarks = benchmarks if benchmarks is not None else _read_benchmarks(gen_dir or GEN)
    errs = validate_exclusions(spec, pilot_dir or PILOT, benchmarks)
    if errs:
        raise EvaluationExclusionError(f"{path}: {len(errs)} problem(s):\n  - " + "\n  - ".join(errs))
    return spec, exclusions_sha256(path)


def excluded_ids(path=None):
    """The excluded item IDs (structure-checked only). Used by the independent row guard."""
    spec = _read_json(path or EXCLUSIONS_FILE)
    ids = [it.get("item_id") for it in spec.get("exclusions") or []]
    if spec.get("schema") != SCHEMA or not ids or not all(isinstance(i, str) and i for i in ids):
        raise EvaluationExclusionError("exclusion file is malformed; refusing to compute metrics")
    return frozenset(ids)


def assert_no_excluded(rows, where, path=None):
    """Raise if any row carries an excluded item ID (defence in depth for every metric computation)."""
    ids = excluded_ids(path)
    leaked = sorted({r["item_id"] for r in rows if r.get("item_id") in ids})
    if leaked:
        raise EvaluationExclusionError(f"{where}: excluded TEST items reached a metric computation: {leaked}")


class TestItems:
    """Scored TEST rows after exclusion, with the audit trail of removed rows."""
    __test__ = False  # not a pytest class

    def __init__(self, product, country, excluded, spec, sha256):
        self.product, self.country, self.excluded, self.spec, self.sha256 = product, country, excluded, spec, sha256

    def sibling_clusters(self, benchmark):
        return frozenset(self.spec["sensitivity_sibling_clusters"][benchmark])


def load_test_items(expected_sha256, gen_dir=None, path=None, pilot_dir=None):
    """THE choke point: the only supported way to obtain TEST rows for any metric.

    `expected_sha256` must be the exclusion file hash recorded in the freeze manifest; a missing or
    different hash stops evaluation."""
    path = path or EXCLUSIONS_FILE
    if not expected_sha256:
        raise EvaluationExclusionError("TEST evaluation requires the exclusion file SHA-256 from the freeze manifest")
    actual = exclusions_sha256(path)
    if actual != expected_sha256:
        raise EvaluationExclusionError(f"exclusion file hash {actual} does not match the manifest ({expected_sha256})")
    benchmarks = _read_benchmarks(gen_dir or GEN)
    spec, sha = load_exclusions(path, pilot_dir=pilot_dir, benchmarks=benchmarks)
    ids = {it["item_id"] for it in spec["exclusions"]}
    meta = {it["item_id"]: it for it in spec["exclusions"]}
    scored, excluded = {}, []
    for name, rows in benchmarks.items():
        test = [r for r in rows if r["split"] == "test"]
        scored[name] = [r for r in test if r["item_id"] not in ids]
        removed = [r for r in test if r["item_id"] in ids]
        expect = sum(1 for it in spec["exclusions"] if it["benchmark"] == name)
        if len(removed) != expect or len(scored[name]) != len(test) - expect:
            raise EvaluationExclusionError(f"{name}: removed {len(removed)} rows, expected {expect}")
        for r in removed:
            m = meta[r["item_id"]]
            excluded.append({"benchmark": name, "pilot_id": m["pilot_id"], "item_id": r["item_id"],
                             "split": r["split"], "category": r["subset"], "cluster": r["cluster"],
                             "text": r["text"], "reason": m["reason"], "source_record": m["source_record"],
                             "exclusions_sha256": sha})
    return TestItems(scored["product"], scored["country"], excluded, spec, sha)


def without_sibling_clusters(rows, clusters):
    """Sensitivity set: drop every row whose cluster is one of the fixed sibling clusters."""
    return [r for r in rows if r["cluster"] not in clusters]


def write_audit(path, excluded):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=AUDIT_FIELDS)
        w.writeheader()
        w.writerows(excluded)
