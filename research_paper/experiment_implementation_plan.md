# Experiment Implementation Plan (Phase 4 — proposed, awaiting approval)

## 1. Branching and safety
- Work branch: `research/option-a-evaluation`, created from `claude/lexitax-audit-ieee-paper-qgqqxm`, which contains the Phase 1 report on top of `main@01dde8b`.
- `main` is untouched. No force-push. Original history preserved.
- Original code stays **byte-identical**: `backend/server.py`, datasets, notebook, frontend. A CI-style check (`tests/test_original_untouched.py`) compares SHA-256 hashes of these files against `main@01dde8b`.

## 2. Three layers kept distinct
| Layer | Location | Content |
|---|---|---|
| Original implementation | `backend/`, root datasets, `frontend/` | Unchanged. B and S0 are imported from `backend/server.py` as-is. |
| Research implementation (S1) | `backend/lexitax_v2/` (new package, new files only) | `validation.py`, `jurisdiction.py`, `product.py`, `pipeline.py`. Reuses `PolicyRetriever` and the tax/calculation formula from the original module. |
| Evaluation infrastructure | `research_paper/experiments/` | Benchmark builders, runners, metrics, statistics, figures, results, logs |

**Optional app integration (needs approval, listed separately in §6):**
- an `/api/v2/audit` endpoint;
- relabelling the hard-coded claims in `SystemBenchmark.jsx`.

## 3. S1 design (exact)
1. **Validation:**
   - `product_name` and `destination` are non-empty after strip;
   - `price > 0` and finite;
   - `quantity` is an integer ≥ 1 (accepting integral floats such as 2.0);
   - `shipping ≥ 0` and finite.
   - Otherwise return `INVALID_INPUT(reason)`.
2. **Jurisdiction:**
   - Normalise: casefold, strip, collapse whitespace, remove accents and punctuation except hyphens.
   - Match against the 40 canonical names, then against the ISO alias table (alpha-2, alpha-3, `name`, `official_name`, `common_name` of the 40 supported countries).
   - If the string instead matches an ISO entry of a *non-supported* country → `UNSUPPORTED_JURISDICTION`. Otherwise → `UNRESOLVED_JURISDICTION`.
   - No substring or fuzzy matching by default.
3. **Product:**
   - Normalise as above. An exact match to a catalogue product name or base-type name gives a score of 1.0.
   - Otherwise compute character-trigram TF-IDF cosine against all 1,200 product names and 60 base-type names (word-boundary padded), using the same IDF smoothing as the original retriever, so the method is consistent with the codebase.
   - Take the best base type. If score < τ → `UNRESOLVED_PRODUCT` (abstain).
   - τ is chosen on PRB-dev as the smallest threshold whose dev selective risk ≤ 5 % (rule fixed in advance). The full curve is reported.
4. **Tax, calculation, policy:** identical functions and tables to S0. Missing FX rates return `null` with a flag instead of 1.0.
5. **Output:** `status ∈ {RESOLVED, ABSTAINED, INVALID_INPUT}`, `reasons[]`, and a per-stage trace with method and score.

Dependencies:
- `pycountry==26.2.16` (LGPL-2.1; data from iso-codes) — S1 runtime.
- `numpy`, `pandas`, `scipy`, `matplotlib` — evaluation only.
- Pinned in `research_paper/experiments/requirements.txt`.

`rapidfuzz` was considered and rejected: the in-house trigram TF-IDF keeps the method transparent and dependency-light.

## 4. Evaluation code layout
```
research_paper/experiments/
  requirements.txt  run_all.py  config.yaml  README.md
  build/        build_prb.py  build_jrb.py  build_e2e.py  build_malformed.py
  data/         external/hs2022.csv (+SHA)  prb_*.csv  jrb_*.csv  e2e.csv  MANIFEST.json
  annotation/   P5_writer.csv  P5_blind.csv  P5_annot.csv  J5_*.csv  adjudication.csv
  systems/      adapters.py   (B, S0, S1, ablation variants; uniform interface)
  eval/         metrics.py  stats.py (Wilson, McNemar-exact, Holm, kappa, bootstrap)  latency.py
  results/      raw/*.jsonl  processed/*.csv  REPORT.md  env.json
  figures/      risk_coverage.pdf  architecture.pdf
  tests/        test_metrics.py  test_original_untouched.py  test_s1_unit.py  test_determinism.py
```

## 5. Execution
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r research_paper/experiments/requirements.txt
python research_paper/experiments/run_all.py --stage build      # benchmarks (except human subsets)
python research_paper/experiments/run_all.py --stage annotate   # creates blind files, computes kappa after labelling
python research_paper/experiments/run_all.py --stage freeze     # hashes into MANIFEST.json
python research_paper/experiments/run_all.py --stage evaluate   # systems, ablations, stats, figures, REPORT.md
pytest research_paper/experiments/tests
```

## 6. Proposed application changes (each needs a yes/no)
| # | Change | Why | Risk |
|---|---|---|---|
| C1 | Add `backend/lexitax_v2/` (S1) as new files | Research system under test; the improvements are real fixes of the defects found in Phase 1 | None to the original code |
| C2 | Add `/api/v2/audit` route in `server.py` (additive, ~20 lines) | Lets the app use S1; keeps v1 routes intact | Small edit to an original file |
| C3 | Relabel `SystemBenchmark.jsx`: remove "0 % False Negatives", "37.5 %/100 %" or label them as an illustrative capability checklist | These are hard-coded, not measured | UI text change |
| C4 | Leave the README unchanged (the authors may revise it themselves) | Not in scope | — |

If C2 and C3 are declined, S1 is evaluated as a library and the app stays exactly as it is.
