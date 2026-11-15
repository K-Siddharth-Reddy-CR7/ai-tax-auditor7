# LEXITAX AUDIT — resolution study: evaluation infrastructure

Compares **B** (original single-step baseline), **S0** (original staged pipeline) and **S1** (`backend/lexitax_v2`, corrected staged pipeline) on product (HS-6) resolution, country identification, tax-data availability and downstream error propagation.

## Status
- Benchmarks under `data/generated/` are a **DRAFT v4** build (product 809, country 2,122, malformed 18). They are **not frozen** and **no evaluation has been run**.
- Design: `dataset_sampling_rationale.md`. Provenance: `data_provenance.md`. Human review: `pilot_review_sheet.md` (10 items) and `p7_review_sheet.md` (P7). Decisions: `../phase7_methodology_decisions.md`.
- `tune` and `evaluate` refuse to run until the benchmarks are frozen with `--approved-by`. Freezing happens after the authors sign off the 10-item pilot (`pilot/`).

## Reproduce
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r research_paper/experiments/requirements.txt
cd research_paper/experiments
export PYTHONDONTWRITEBYTECODE=1
python run_all.py --stage build      # deterministic (seed in config.json)
python run_all.py --stage validate   # -> data/generated/VALIDATION_REPORT.md
python run_all.py --stage smoke      # L0==S0, L5==S1 on 400 canonical transactions
python run_all.py --stage pilot      # -> pilot/pilot_review_sheet.csv
python -m pytest -q tests ../../backend/tests
# after pilot sign-off:
python run_all.py --stage freeze --approved-by "<author name>"
python run_all.py --stage tune       # DEV split only -> results/tuning_dev.json
python run_all.py --stage evaluate   # TEST split -> results/processed/*.csv, latency.json
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
