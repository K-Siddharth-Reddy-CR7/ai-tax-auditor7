"""Synthetic frozen-manifest fixtures for TEST-run tests (temporary directories only; never the real results/).

Phase C.1: the code identity is taken from a TEMPORARY git repository holding copies of the real files matched
by run_control.CODE_IDENTITY_PATTERNS, so tests never depend on the state of the real working tree.
"""
import glob
import json
import os
import shutil
import subprocess

from lexeval.paths import EXP, PILOT, REPO
from lexeval.run_control import CODE_IDENTITY_PATTERNS, EXCLUDED_FILE, RunPaths, manifest_record

GIT = ["git", "-c", "user.name=synthetic", "-c", "user.email=synthetic@example.invalid", "-c", "commit.gpgsign=false"]


def git(repo, *args):
    return subprocess.run(GIT + ["-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


def make_code_repo(dest):
    """A temporary git repository with copies of the code-identity files, committed (clean tree)."""
    dest = str(dest)
    os.makedirs(dest, exist_ok=True)
    for pat in CODE_IDENTITY_PATTERNS:
        for p in glob.glob(os.path.join(REPO, pat), recursive=True):  # same expansion as code_identity
            rel = os.path.relpath(p, REPO)
            os.makedirs(os.path.dirname(os.path.join(dest, rel)), exist_ok=True)
            shutil.copy2(p, os.path.join(dest, rel))
    with open(os.path.join(dest, "README_synthetic.txt"), "w") as fh:
        fh.write("synthetic code repository for tests\n")
    git(dest, "init", "-q")
    git(dest, "add", "-A")
    git(dest, "commit", "-q", "-m", "synthetic frozen code")
    return dest


def make_paths(tmp, gen_dir, exclusions_path, pilot_dir, *, omit=None, tuning_split="dev", write_manifest=True):
    """Write a synthetic manifest (and dummy malformed/audit files, a DEV tuning record) for `gen_dir`.

    The real config.json and decisions file are only hashed. `omit` drops one manifest key."""
    for f in ("malformed_inputs.csv", EXCLUDED_FILE):
        p = os.path.join(gen_dir, f)
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("synthetic\n")
    results = os.path.join(str(tmp), "results")
    os.makedirs(results, exist_ok=True)
    code = os.path.join(str(tmp), "code")
    if not os.path.isdir(code):
        make_code_repo(code)
    paths = RunPaths(gen=gen_dir, manifest=os.path.join(gen_dir, "MANIFEST.json"),
                     config=os.path.join(EXP, "config.json"),
                     treatments=os.path.join(PILOT, "authorised_review_treatments_v1.csv"),
                     exclusions=exclusions_path, pilot=pilot_dir, results=results, code_root=code)
    if write_manifest:
        man = manifest_record(paths, "synthetic test")
        if omit:
            man.pop(omit)
        with open(paths.manifest, "w", encoding="utf-8") as fh:
            json.dump(man, fh)
    with open(paths.tuning, "w", encoding="utf-8") as fh:
        json.dump({"split": tuning_split, "chosen": {"product_min_coverage": 0.5, "product_typo_max_edits": 1,
                                                     "product_typo_min_len": 5}}, fh)
    return paths
