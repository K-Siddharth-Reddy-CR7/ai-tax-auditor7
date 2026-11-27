"""Selection of S1's product parameters on the DEV split only (pre-declared rule, config.json `tuning_rule`).

Rule (STRICT, author decision 15 Nov 2026; not to be relaxed after observing results): maximise DEV macro
decision-accuracy over product categories P2-P7, subject to DEV macro silent-error rate <= that of baseline B on
DEV. If no setting satisfies the constraint, report this honestly and select the setting with minimum DEV macro
silent-error rate. Ties -> larger coverage threshold, fewer typo edits, longer minimum length.

Tie-breaks (documented 26 Nov 2026 as a clarification of the existing deterministic behaviour, Phase C.1):
- feasible case: highest DEV macro decision accuracy; ties -> larger coverage threshold, fewer typo edits, longer
  minimum length (FEASIBLE_ORDER);
- no feasible setting: lowest DEV macro silent-error rate; if tied, higher DEV macro decision accuracy; then the
  same three tie-breaks (INFEASIBLE_ORDER).

Phase C safeguards: every row that reaches selection must carry split == "dev" (missing, empty, "test" or mixed
splits raise TuningSplitError, whatever the input path); the record states split "dev" and is never overwritten.
For the DEV risk-coverage figure the same grid is also summarised over DEV P1-P7 (the primary pooled product
scope); these figure metrics do NOT enter selection.
"""
import hashlib
import itertools
import json
import os
from collections import defaultdict

from lexitax_v2 import S1Config
from lexitax_v2.product import resolve_product

from . import scoring
from .build_common import read_csv
from .paths import GEN, RESULTS
from .systems import run_B

SELECTION_EXCLUDED_SUBSETS = ("P1_exact", "P8_hs_formal")  # P1 trivial; P8 reported separately
FIGURE_EXCLUDED_SUBSETS = ("P8_hs_formal",)                # primary pooled product scope = P1-P7
FEASIBLE_ORDER = ("highest DEV macro decision accuracy", "larger product_min_coverage",
                  "fewer product_typo_max_edits", "longer product_typo_min_len")
INFEASIBLE_ORDER = ("lowest DEV macro silent-error rate", "higher DEV macro decision accuracy",
                    "larger product_min_coverage", "fewer product_typo_max_edits", "longer product_typo_min_len")


class TuningSplitError(ValueError):
    """A non-DEV row reached the tuning code."""


class TuningRecordError(ValueError):
    """The tuning record changed after it was hashed, or is not a DEV record."""


def assert_dev_only(rows, where="tuning"):
    if not rows:
        raise TuningSplitError(f"{where}: no DEV rows")
    bad = sorted({repr(r.get("split")) for r in rows if r.get("split") != "dev"})
    if bad:
        raise TuningSplitError(f"{where}: only split 'dev' rows are allowed; found split values {bad}")
    return rows


def load_dev_rows(gen_dir=None):
    """All DEV product rows of the benchmark (TEST rows are never returned)."""
    rows = [r for r in read_csv(os.path.join(gen_dir or GEN, "product_benchmark.csv")) if r.get("split") == "dev"]
    return assert_dev_only(rows, "load_dev_rows")


def _macro(item_outcomes):
    by_subset = defaultdict(list)
    for subset, o in item_outcomes:
        by_subset[subset].append(o)
    acc = [scoring.summarise(v)["decision_accuracy"] for v in by_subset.values()]
    ser = [scoring.summarise(v)["silent_error_rate"] for v in by_subset.values()]
    return sum(acc) / len(acc), sum(ser) / len(ser)


def select(results, b_ser):
    """Apply the pre-declared rule to grid results. Returns (chosen, rule_applied)."""
    feasible = [r for r in results if r["dev_macro_silent_error_rate"] <= b_ser + 1e-12]
    tiebreak = lambda r: (r["product_min_coverage"], -r["product_typo_max_edits"], r["product_typo_min_len"])  # noqa: E731
    if feasible:
        return (max(feasible, key=lambda r: (r["dev_macro_decision_accuracy"], tiebreak(r))),
                "max dev accuracy s.t. dev SER <= SER(B)")
    return (min(results, key=lambda r: (r["dev_macro_silent_error_rate"], -r["dev_macro_decision_accuracy"],
                                        tuple(-x for x in tiebreak(r)))),
            "infeasible -> min dev SER (no setting met the constraint; reported as such)")


def grid_settings(grid):
    for cov, k, m in itertools.product(grid["product_min_coverage"], grid["product_typo_max_edits"],
                                       grid["product_typo_min_len"]):
        if k == 0 and m != grid["product_typo_min_len"][0]:
            continue  # min_len irrelevant without typo tolerance
        yield cov, k, m


def tune(cfg, rows=None, gen_dir=None, out_path=None):
    """Select S1's parameters on DEV and write the tuning record (exclusive-create)."""
    source = "rows supplied by caller"
    if rows is None:
        rows = load_dev_rows(gen_dir)
        path = os.path.join(gen_dir or GEN, "product_benchmark.csv")
        source = f"product_benchmark.csv sha256={hashlib.sha256(open(path, 'rb').read()).hexdigest()}"
    assert_dev_only(rows, "tune")
    pooled = [r for r in rows if r["subset"] not in FIGURE_EXCLUDED_SUBSETS]
    dev = [r for r in pooled if r["subset"] not in SELECTION_EXCLUDED_SUBSETS]
    assert_dev_only(dev, "tune(selection rows)")
    b_out = [(it["subset"], scoring.product_outcome(it, run_B(it["text"], "India", 100, 1, 0))) for it in dev]
    b_acc, b_ser = _macro(b_out)
    results = []
    for cov, k, m in grid_settings(cfg["tuning_grid"]):
        outs = {}
        for it in pooled:
            r = resolve_product(it["text"], cov, k, m)
            std = {"status": "OK", "prod_hs": r["hs_code"] if r["status"] == "RESOLVED" else None}
            outs[it["item_id"]] = scoring.product_outcome(it, std)
        acc, ser = _macro([(it["subset"], outs[it["item_id"]]) for it in dev])
        fig = scoring.summarise([outs[it["item_id"]] for it in pooled])
        results.append(dict(product_min_coverage=cov, product_typo_max_edits=k, product_typo_min_len=m,
                            dev_macro_decision_accuracy=acc, dev_macro_silent_error_rate=ser,
                            dev_pooled_P1_P7={"n": fig["n"], "coverage": fig["coverage"],
                                              "silent_error_rate": fig["silent_error_rate"],
                                              "selective_risk": (fig[scoring.SILENT] / fig["answered"]
                                                                 if fig["answered"] else None)}))
    chosen, rule = select(results, b_ser)
    ids = sorted(r["item_id"] for r in rows)
    record = {"split": "dev", "tuning_rule": cfg["tuning_rule"], "rule_applied": rule, "chosen": chosen,
              "baseline_B_dev_macro_accuracy": b_acc, "baseline_B_dev_macro_ser": b_ser,
              "grid_definition": cfg["tuning_grid"], "grid": results,
              "n_dev_items_selection_P2_P7": len(dev), "n_dev_items_pooled_P1_P7": len(pooled),
              "dev_item_ids_sha256": hashlib.sha256("\n".join(ids).encode()).hexdigest(), "input": source,
              "tie_breaks": {"feasible": list(FEASIBLE_ORDER), "infeasible": list(INFEASIBLE_ORDER)},
              "note": "Selection uses DEV macro metrics over P2-P7 only. dev_pooled_P1_P7 values are for the DEV "
                      "risk-coverage figure (development analysis) and play no role in selection."}
    out_path = out_path or os.path.join(RESULTS, "tuning_dev.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "x", encoding="utf-8") as fh:  # never overwrite an earlier selection
        json.dump(record, fh, indent=2)
    return S1Config(product_min_coverage=chosen["product_min_coverage"],
                    product_typo_max_edits=chosen["product_typo_max_edits"],
                    product_typo_min_len=chosen["product_typo_min_len"]), record


def load_tuned(path=None, expected_sha256=None):
    """Load the chosen S1Config. With expected_sha256 (TEST runs: the hash recorded when the run was opened),
    the exact bytes parsed are hashed first, so a record changed in between is refused."""
    with open(path or os.path.join(RESULTS, "tuning_dev.json"), "rb") as fh:
        data = fh.read()
    if expected_sha256 is not None and hashlib.sha256(data).hexdigest() != expected_sha256:
        raise TuningRecordError("tuning record changed after the TEST run was opened")
    rec = json.loads(data)
    if rec.get("split") != "dev":
        raise TuningSplitError("tuning record is not a DEV-only record")
    c = rec["chosen"]
    return S1Config(product_min_coverage=c["product_min_coverage"],
                    product_typo_max_edits=c["product_typo_max_edits"],
                    product_typo_min_len=c["product_typo_min_len"])


def _setting(g):
    return (g["product_min_coverage"], g["product_typo_max_edits"], g["product_typo_min_len"])


def _diff(a, b):
    return None if a is None or b is None else a - b


def full_pipeline_grid(cfg, tuning_record, gen_dir=None, out_path=None):
    """Figure/sensitivity only (Phase C.1; never used for selection): every tuning-grid setting run through
    the FULL S1 pipeline on the same DEV product inputs, adapter and definitions as the DEV system evaluation.

    Records, per setting, the resolver-level scores (from the tuning record, which drove selection), the
    full-pipeline scores, and their differences (full minus resolver); plus the selected setting and its
    full-pipeline operating point. Differences are preserved as computed, never forced to zero."""
    from . import evaluate
    from .systems import run_S1
    if tuning_record.get("split") != "dev":
        raise TuningRecordError("tuning record is not a DEV-only record")
    p_items, _, _, _ = evaluate.load("dev", gen_dir=gen_dir)
    assert_dev_only(p_items, "full_pipeline_grid")
    settings = list(grid_settings(cfg["tuning_grid"]))
    resolver = {_setting(g): g for g in tuning_record["grid"]}
    if set(resolver) != set(settings):
        raise TuningRecordError("tuning record grid differs from the configured grid")
    names = {s: f"S1[cov={s[0]},edits={s[1]},min_len={s[2]}]" for s in settings}
    systems = {names[s]: (lambda c: (lambda *a: run_S1(*a, config=c)))(
        S1Config(product_min_coverage=s[0], product_typo_max_edits=s[1], product_typo_min_len=s[2]))
        for s in settings}
    rows = evaluate.run_product_task(p_items, systems)
    grid = []
    for s in settings:
        rs = [r for r in rows if r["system"] == names[s]]
        pooled = scoring.summarise([r["outcome"] for r in rs if r["subset"] not in FIGURE_EXCLUDED_SUBSETS])
        acc, ser = _macro([(r["subset"], r["outcome"]) for r in rs if r["subset"] not in SELECTION_EXCLUDED_SUBSETS])
        full = {"dev_macro_decision_accuracy": acc, "dev_macro_silent_error_rate": ser,
                "dev_pooled_P1_P7": {"n": pooled["n"], "coverage": pooled["coverage"],
                                     "silent_error_rate": pooled["silent_error_rate"],
                                     "selective_risk": (pooled[scoring.SILENT] / pooled["answered"]
                                                        if pooled["answered"] else None)}}
        res = resolver[s]
        rp, fp = res["dev_pooled_P1_P7"], full["dev_pooled_P1_P7"]
        diff = {"dev_macro_decision_accuracy": _diff(acc, res["dev_macro_decision_accuracy"]),
                "dev_macro_silent_error_rate": _diff(ser, res["dev_macro_silent_error_rate"]),
                "coverage": _diff(fp["coverage"], rp["coverage"]),
                "silent_error_rate": _diff(fp["silent_error_rate"], rp["silent_error_rate"]),
                "selective_risk": _diff(fp["selective_risk"], rp["selective_risk"])}
        grid.append({"product_min_coverage": s[0], "product_typo_max_edits": s[1], "product_typo_min_len": s[2],
                     "resolver_level": {k: res[k] for k in ("dev_macro_decision_accuracy",
                                                            "dev_macro_silent_error_rate", "dev_pooled_P1_P7")},
                     "full_pipeline": full, "difference_full_minus_resolver": diff})
    chosen = _setting(tuning_record["chosen"])
    sel = next(g for g in grid if _setting(g) == chosen)
    nonzero = [g for g in grid if any(v not in (None, 0, 0.0) for v in g["difference_full_minus_resolver"].values())]
    out = {"split": "dev",
           "purpose": "S1 full-pipeline risk-coverage across the tuning grid (DEV): figure and sensitivity only",
           "selection_basis": "resolver-level DEV macro scores over P2-P7 (pre-declared rule; unchanged)",
           "selected_setting": tuning_record["chosen"], "rule_applied": tuning_record["rule_applied"],
           "selected_full_pipeline_point": sel["full_pipeline"],
           "n_settings": len(grid), "n_settings_with_differences": len(nonzero), "grid": grid,
           "n_dev_product_items": len(p_items)}
    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "x", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2)
    return out
