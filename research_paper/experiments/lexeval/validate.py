"""Dataset validation: provenance completeness, duplicates, conflicts, cross-split leakage."""
import os
from collections import Counter, defaultdict

from lexitax_v2.normalize import canonical

from .build_common import read_csv
from .paths import GEN
from .refdata import load_hs6


def _jaccard(a, b):
    return len(a & b) / len(a | b) if a | b else 0.0


def validate():
    hs6, _ = load_hs6()
    report = {"errors": [], "warnings": [], "stats": {}}
    for name, label_fields in (("product_benchmark.csv", ("expected", "label_hs")),
                               ("country_benchmark.csv", ("gold_iso", "label_kind"))):
        rows = read_csv(os.path.join(GEN, name))
        st = report["stats"][name] = {}
        st["n"] = len(rows)
        st["by_subset_split"] = dict(Counter(f"{r['subset']}/{r['split']}" for r in rows))
        for r in rows:
            if not r["label_source"] or not r["group"] or r["split"] not in ("dev", "test"):
                report["errors"].append(f"{name}:{r['item_id']} missing provenance/group/split")
            if name.startswith("product") and r["expected"] == "ANSWER":
                if r["label_hs"] not in hs6 and r["subset"] != "PA":
                    report["errors"].append(f"{r['item_id']} label HS not in reference")
                if r["subset"] == "PA" and r["hs_exists"] != "True":
                    report["warnings"].append(f"{r['item_id']} catalogue HS not in reference")
        canon = defaultdict(set)
        labels = defaultdict(set)
        for r in rows:
            k = canonical(r["text"])
            canon[k].add(r["split"])
            labels[k].add(tuple(r[f] for f in label_fields))
        st["texts_in_both_splits"] = sum(1 for v in canon.values() if len(v) > 1)
        st["conflicting_label_texts"] = sum(1 for v in labels.values() if len(v) > 1)
        if st["texts_in_both_splits"]:
            report["errors"].append(f"{name}: {st['texts_in_both_splits']} identical texts across splits")
        if st["conflicting_label_texts"]:
            report["errors"].append(f"{name}: {st['conflicting_label_texts']} texts with conflicting labels")
        groups = defaultdict(set)
        for r in rows:
            groups[r["group"]].add(r["split"])
        st["groups"] = len(groups)
        st["groups_straddling_splits"] = sum(1 for v in groups.values() if len(v) > 1)
        if st["groups_straddling_splits"]:
            report["errors"].append(f"{name}: groups straddle splits")
        # near-duplicates across splits (reported, not removed): token Jaccard >= 0.9 among short texts
        dev = [(r["item_id"], set(canonical(r["text"]).split())) for r in rows if r["split"] == "dev"]
        test = [(r["item_id"], set(canonical(r["text"]).split())) for r in rows if r["split"] == "test"]
        dev_short = [d for d in dev if len(d[1]) <= 12]
        near = 0
        for _, tt in test:
            if len(tt) <= 12 and any(_jaccard(tt, dt) >= 0.9 for _, dt in dev_short):
                near += 1
        st["test_items_with_near_duplicate_in_dev(jaccard>=0.9,<=12 tokens)"] = near
    return report


def write_report(report, build_log, path):
    lines = ["# Dataset validation report (DRAFT build — not frozen)", ""]
    lines.append(f"Errors: {len(report['errors'])}; warnings: {len(report['warnings'])}")
    for e in report["errors"]:
        lines.append(f"- ERROR {e}")
    for w in report["warnings"][:50]:
        lines.append(f"- WARNING {w}")
    for name, st in report["stats"].items():
        lines += ["", f"## {name}"]
        for k, v in st.items():
            lines.append(f"- {k}: {v}")
    lines += ["", "## Build log (pre-declared exclusion rules applied)"]
    c = Counter(k for k, _ in build_log)
    for k, v in sorted(c.items()):
        lines.append(f"- {k}: {v}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
