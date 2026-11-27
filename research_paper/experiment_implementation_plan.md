# Experiment Implementation Plan — v2 (implemented, 14 Nov 2026)

## Status
| Item | State |
|---|---|
| Branch `research/option-a-evaluation` (no force-push, `main` untouched) | ✅ in use |
| C1: S1 package `backend/lexitax_v2/` + 63 tests | ✅ implemented, tests pass |
| C2: `/api/v2/audit` | ⏸ deferred by authors |
| C3: frontend claim corrections | ✅ done (text only; `vite build` OK) — see `IMPLEMENTATION_CHANGES.md` |
| Evaluation infrastructure `research_paper/experiments/` + 13 tests | ✅ implemented |
| Draft benchmarks (product 6,096; country 2,122; malformed 18) | ✅ built and validated (0 errors), **not frozen** |
| 10-item pilot sheet | ✅ prepared; **awaiting two human reviewers** |
| DEV tuning, TEST evaluation, latency, figures | ⛔ blocked by design until freeze |

## Execution
```bash
cd research_paper/experiments
pip install -r requirements.txt
export PYTHONDONTWRITEBYTECODE=1
python run_all.py --stage build && python run_all.py --stage validate
python run_all.py --stage smoke && python run_all.py --stage pilot
python -m pytest -q tests ../../backend/tests
# after pilot sign-off by the authors:
python run_all.py --stage freeze --approved-by "<author>"
python run_all.py --stage tune
python run_all.py --stage evaluate
```

## Environment used for development
- Python 3.13.x; Linux cloud VM with 4 vCPU (Intel Xeon @ 2.10 GHz).
- Pinned packages: `research_paper/experiments/requirements.txt`.
- The evaluation run records the full environment in `results/latency.json`.

## Traceability
| Output | Location |
|---|---|
| Raw per-item system outputs | `results/raw/*.jsonl` |
| Per-item scored rows | `results/processed/*_items.csv` |
| Summaries with Wilson CIs | `results/processed/*_summary.csv` |
| Paired tests with Holm-adjusted p-values | `results/processed/*_paired_tests.csv` |
| DEV tuning record | `results/tuning_dev.json` |

The manuscript may only cite numbers present in these files.

## Remaining engineering (after freeze)
- Run the stages, then write `results/REPORT.md`, a generated summary of the processed CSVs.
- Generate figures:
  - risk–coverage figure (sensitivity grid evaluated on TEST);
  - outcome-share bars;
  - architecture diagram for the paper.
- Optional H2 audit sheet generator (60 items, stratified).
