"""Synthetic frozen-manifest fixtures for TEST-run tests (temporary directories only; never the real results/)."""
import hashlib
import json
import os

from lexeval.paths import EXP, PILOT
from lexeval.run_control import DATA_FILES, EXCLUDED_FILE, RunPaths


def _sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def make_paths(tmp, gen_dir, exclusions_path, pilot_dir, *, omit=None, tuning_split="dev"):
    """Write a synthetic manifest (and dummy malformed/audit files, a DEV tuning record) for `gen_dir`.

    The real config.json and decisions file are only hashed. `omit` drops one manifest key."""
    for f in ("malformed_inputs.csv", EXCLUDED_FILE):
        p = os.path.join(gen_dir, f)
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("synthetic\n")
    results = os.path.join(str(tmp), "results")
    os.makedirs(results, exist_ok=True)
    paths = RunPaths(gen=gen_dir, manifest=os.path.join(gen_dir, "MANIFEST.json"),
                     config=os.path.join(EXP, "config.json"),
                     treatments=os.path.join(PILOT, "authorised_review_treatments_v1.csv"),
                     exclusions=exclusions_path, pilot=pilot_dir, results=results)
    man = {"approved_by": "synthetic test",
           "files": {f: _sha(os.path.join(gen_dir, f)) for f in DATA_FILES + [EXCLUDED_FILE]},
           "config_sha256": _sha(paths.config), "review_treatments_sha256": _sha(paths.treatments),
           "evaluation_exclusions_sha256": _sha(exclusions_path)}
    if omit:
        man.pop(omit)
    with open(paths.manifest, "w", encoding="utf-8") as fh:
        json.dump(man, fh)
    with open(paths.tuning, "w", encoding="utf-8") as fh:
        json.dump({"split": tuning_split, "chosen": {"product_min_coverage": 0.5, "product_typo_max_edits": 1,
                                                     "product_typo_min_len": 5}}, fh)
    return paths
