"""Shared dataset-building utilities: dedup/conflict rules and CSV I/O."""
import csv
import os

from lexitax_v2.normalize import canonical

from .splits import split_of


def finalize(items, label_key, seed, dev_fraction, log):
    """Pre-declared rules: (1) drop items whose canonical text is empty;
    (2) if the same canonical (normalised) text carries different expected labels -> drop all copies;
    (3) exact duplicates (identical raw text and label) -> keep first (surface variants such as
        case/whitespace are kept because systems may treat them differently); (4) split by group."""
    by_text = {}
    for it in items:
        key = canonical(it["text"])
        if not key:
            log.append(("empty_after_normalisation", it["item_id"]))
            continue
        by_text.setdefault(key, []).append(it)
    out = []
    for key, group in by_text.items():
        labels = {g[label_key] for g in group}
        if len(labels) > 1:
            for g in group:
                log.append(("label_conflict_removed", g["item_id"]))
            continue
        seen = set()
        for g in group:
            if g["text"] in seen:
                log.append(("duplicate_removed", g["item_id"]))
                continue
            seen.add(g["text"])
            out.append(g)
    for it in out:
        it["split"] = split_of(it["group"], seed, dev_fraction)
    out.sort(key=lambda r: r["item_id"])
    return out


def write_csv(path, rows, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))
