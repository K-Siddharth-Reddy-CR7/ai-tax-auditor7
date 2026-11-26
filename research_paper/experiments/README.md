# LEXITAX AUDIT — resolution study: evaluation infrastructure

Compares **B** (original single-step baseline), **S0** (original staged pipeline) and **S1** (`backend/lexitax_v2`, corrected staged pipeline) on product (HS-6) resolution, country identification, tax-data availability and downstream error propagation.

## Status
- Benchmarks under `data/generated/` are a **DRAFT v4** build (product 809, country 2,122, malformed 18). They are **not frozen** and **no evaluation has been run**.
- Design: `dataset_sampling_rationale.md`. Provenance: `data_provenance.md`. Human review: `pilot_review_sheet.md` (10 items) and `p7_review_sheet.md` (P7). Decisions: `../phase7_methodology_decisions.md`.
- `tune` and `evaluate` refuse to run until the benchmarks are frozen with `--approved-by`. Freezing happens after the authors sign off the 10-item pilot (`pilot/`).
- P7 review decisions are applied only from `pilot/authorised_review_treatments_v1.csv`, validated against the review records. `build` writes the full rows of excluded items to `data/generated/excluded_items.csv`. `freeze` refuses unless the benchmark, that audit file and `build_log.json` match the decisions file.
- TEST rows are obtained only through `lexeval/eval_exclusions.load_test_items()`. It removes the 8 pilot-inspected items listed in `evaluation_exclusions_v1.json`, and requires that file's SHA-256 from the freeze manifest. Every metric function rejects rows with an excluded ID. Sibling-cluster sensitivity outputs are written separately.

## Reproduce
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r research_paper/experiments/requirements.txt
cd research_paper/experiments
export PYTHONDONTWRITEBYTECODE=1
python run_all.py --stage build      # deterministic (seed in config.json)
python run_all.py --stage validate   # -> data/generated/VALIDATION_REPORT.md
python run_all.py --stage smoke      # L0==S0, L5==S1 on 400 canonical transactions
python run_all.py --stage pilot      # creates review sheets only if absent; never overwrites
python -m pytest -q tests ../../backend/tests
# after pilot sign-off:
python run_all.py --stage freeze --approved-by "<author name>"
python run_all.py --stage tune       # DEV only -> results/tuning_dev.json, results/dev/ (DEV risk-coverage figure)
python run_all.py --stage latency    # DEV only -> results/latency_dev.json (product and country workloads)
python run_all.py --stage evaluate --split test --authorised-by "<name>"   # the only TEST route
#   -> results/runs/<run_id>/ (permanent, read-only), logged in results/test_runs.jsonl
#   a further TEST run additionally needs --rerun-reason "<why>"
```

## Layout
| Path | Content |
|---|---|
| `config.json` | Seed, split fraction, perturbations, CLDR locales, tuning grid and pre-declared selection rule |
| `data/external/` | HS 2022 file (unmodified), `PROVENANCE.md` |
| `lexeval/build_*.py` | Benchmark generators. Labels come from reference data or rules, never from system output |
| `lexeval/systems.py` | Adapters for B, S0, S1. The ladder L0→L5 changes one component per step. Extra ablations |
| `lexeval/scoring.py` | Outcome taxonomy: CORRECT, SAFE_ABSTENTION, OVER_ABSTENTION, EXPLICIT_FAILURE, SILENT_ERROR |
| `lexeval/evaluate.py` | Product / country / malformed runs, propagation classes, Wilson CIs, exact McNemar plus Holm |
| `lexeval/tuning.py` | DEV-only parameter selection for S1 |
| `lexeval/latency.py` | Repeated in-process timing with recorded environment |
| `lexeval/figures.py` | Figures generated only from processed results |
| `tests/` | Statistics, scoring, ladder equivalence, build determinism, code-path dry run |
