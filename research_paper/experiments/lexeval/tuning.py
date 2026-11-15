"""Selection of S1's product parameters on the DEV split only (pre-declared rule)."""
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


def _macro(item_outcomes):
    by_subset = defaultdict(list)
    for subset, o in item_outcomes:
        by_subset[subset].append(o)
    acc = [scoring.summarise(v)["decision_accuracy"] for v in by_subset.values()]
    ser = [scoring.summarise(v)["silent_error_rate"] for v in by_subset.values()]
    return sum(acc) / len(acc), sum(ser) / len(ser)


def tune(cfg):
    # P1 (trivial exact names) and P8 (formal HS texts, reported separately) do not drive selection
    dev = [r for r in read_csv(os.path.join(GEN, "product_benchmark.csv"))
           if r["split"] == "dev" and r["subset"] not in ("P1_exact", "P8_hs_formal")]
    b_out = [(it["subset"], scoring.product_outcome(it, run_B(it["text"], "India", 100, 1, 0))) for it in dev]
    b_acc, b_ser = _macro(b_out)
    grid = cfg["tuning_grid"]
    results = []
    for cov, k, m in itertools.product(grid["product_min_coverage"], grid["product_typo_max_edits"],
                                       grid["product_typo_min_len"]):
        if k == 0 and m != grid["product_typo_min_len"][0]:
            continue  # min_len irrelevant without typo tolerance
        outs = []
        for it in dev:
            r = resolve_product(it["text"], cov, k, m)
            std = {"status": "OK", "prod_hs": r["hs_code"] if r["status"] == "RESOLVED" else None}
            outs.append((it["subset"], scoring.product_outcome(it, std)))
        acc, ser = _macro(outs)
        results.append(dict(product_min_coverage=cov, product_typo_max_edits=k, product_typo_min_len=m,
                            dev_macro_decision_accuracy=acc, dev_macro_silent_error_rate=ser))
    feasible = [r for r in results if r["dev_macro_silent_error_rate"] <= b_ser + 1e-12]
    tiebreak = lambda r: (r["product_min_coverage"], -r["product_typo_max_edits"], r["product_typo_min_len"])  # noqa: E731
    if feasible:
        chosen = max(feasible, key=lambda r: (r["dev_macro_decision_accuracy"], tiebreak(r)))
        rule = "max dev accuracy s.t. dev SER <= SER(B)"
    else:
        chosen = min(results, key=lambda r: (r["dev_macro_silent_error_rate"], -r["dev_macro_decision_accuracy"],
                                             tuple(-x for x in tiebreak(r))))
        rule = "infeasible -> min dev SER"
    record = {"baseline_B_dev_macro_accuracy": b_acc, "baseline_B_dev_macro_ser": b_ser,
              "rule_applied": rule, "chosen": chosen, "grid": results, "n_dev_items": len(dev)}
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "tuning_dev.json"), "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2)
    return S1Config(product_min_coverage=chosen["product_min_coverage"],
                    product_typo_max_edits=chosen["product_typo_max_edits"],
                    product_typo_min_len=chosen["product_typo_min_len"]), record


def load_tuned():
    with open(os.path.join(RESULTS, "tuning_dev.json"), encoding="utf-8") as fh:
        c = json.load(fh)["chosen"]
    return S1Config(product_min_coverage=c["product_min_coverage"],
                    product_typo_max_edits=c["product_typo_max_edits"],
                    product_typo_min_len=c["product_typo_min_len"])
