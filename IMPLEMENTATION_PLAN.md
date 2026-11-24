# IMPLEMENTATION_PLAN.md — applying the review decisions and evaluation safeguards

**Status: PLAN ONLY. IMPLEMENTATION HAS NOT BEEN AUTHORISED.**
- No code, configuration, benchmark row, label, generated file, review record or scan file has been changed by this plan.
- Nothing has been rebuilt, frozen, tuned or evaluated.
- Written 24 Nov 2026 on `research/option-a-evaluation`.
- Read together with `RESEARCH_STATE.md`. Its integrity rules (§0) apply unchanged.

**Verified repository facts this plan relies on:**
- The last commit that changed the generated benchmark, generation code or configuration is **`a0129b8`** (Phase 7, 15 Nov 2026). Verified with `git log -- research_paper/experiments/data/generated research_paper/experiments/lexeval research_paper/experiments/config.json`. Later commits only recorded reviews and documentation; `063c8db` is the documentation checkpoint.
- Current benchmark SHA-256 hashes:
  - product `4b69c5bb…5351`;
  - country `1bf3f489…c929`;
  - malformed `bb3af788…5df`.
- **Existing defects found while planning:**
  1. `lexeval/build_products.py` already applies recorded look-alike decisions whenever any decision exists (`reviewed = any(decisions.values())`). A fresh build would therefore drop the 3 Uncertain look-alikes. Consequently `tests/test_systems_and_data.py::test_build_is_deterministic` **currently fails** (run on 24 Nov 2026 in a temporary directory; generated files were verified unchanged). The "79 passing" figure in older documents is no longer true.
  2. `lexeval/pilot.py::build_plain_scan_sheet` would **overwrite** `pilot/p7_plain_scan_v4.txt` if `run_all.py --stage pilot` were run, because that file still says `REVIEWED: no`.
  3. `run_all.py::stage_freeze` requires `REVIEWED: yes` in the scan file. It ignores the completed record `pilot/p7_plain_scan_progress_v4.csv`, and "Flag for review" has no meaning in code.
- **Until Phase A is implemented, do not run `--stage build`, `--stage pilot` or `--stage freeze`.**

---

## 1. Author decisions on the eight design questions (24 Nov 2026)
1. **Single authoritative decisions file:** `pilot/authorised_review_treatments_v1.csv`. The original review sheets and scan file are preserved unchanged.
2. **Authorised exclusions** are removed from the scored benchmark. Their full original rows and exclusion reasons are kept in an audit file.
3. **Dedicated `evaluation_exclusions_v1.json`** for the eight pilot-reviewed TEST items.
4. **P04 and P08 stay in DEV**, since their pilot labels were accepted.
5. **Sibling sensitivity analysis**, with sibling groups fixed *before* any TEST result is seen, kept separate from the primary evaluation.
6. **Latency never uses the TEST split.** DEV workloads only, with product and country latency reported separately.
7. **TEST-evaluation lock** with immutable run IDs. Reruns must be explicitly authorised and logged. Earlier attempts are never overwritten.
8. **Fix the scan-file overwrite and the freeze guard**, so that they validate the authoritative decisions file and the review records, not the scan file's `REVIEWED` line.

## 2. Authorised P7 exclusions (approved 24 Nov 2026; NOT yet applied)
Each was verified against the review records:

| Item ID | Review | Recorded decision | Authorised treatment | Split | Look-alike |
|---|---|---|---|---|---|
| `P7_outside\|couch and lamp` | look-alike #4 | Uncertain | Exclude (Uncertain) | dev | yes |
| `P7_outside\|toothbrush` | look-alike #14 | Uncertain | Exclude (Uncertain) | test | yes |
| `P7_outside\|video game` | look-alike #15 | Uncertain | Exclude (Uncertain) | dev | yes |
| `P7_outside\|satellite antenna` | plain scan #81 | Flag for review | Exclude (Uncertain), by author decision | test | no |

Retained:
- the 13 Outside look-alikes (gold DECLINE);
- the 99 Clear plain names (gold DECLINE).

## 3. Separate pilot evaluation exclusion (approved in principle; NOT yet implemented)
These eight TEST items were inspected during the labelling-rule pilot. Their rows and labels stay in the benchmark, but they are excluded from **every** final TEST metric. IDs and splits were verified against `pilot/pilot_reviewed_items.json` and the benchmark files.

| Pilot | Item ID | Benchmark | Category |
|---|---|---|---|
| P01 | `P2_format\|Scanner\|ws_punct` | product | P2 |
| P02 | `P3_typo\|Graphics Card\|typo\|0` | product | P3 |
| P03 | `P4_short\|WiFi Adapter\|head_noun` | product | P4 |
| P05 | `P6_ambiguous\|word\|computer` | product | P6 |
| P06 | `P7_outside\|card index` | product | P7 (Outside look-alike, retained) |
| P07 | `P8_hs\|other_chapter\|080122` | product | P8 |
| P09 | `CB\|DZ\|official_name` | country | J3 |
| P10 | `CE\|sint` | country | J6 |

P04 (`P5_confusable|Memory Card|typo_distinguishing_word`) and P08 (`CD|NZ|es`) are in DEV and stay there.

---

## 4. Phased plan
### Phase A — Apply review decisions through a single authoritative file
| Action | Files |
|---|---|
| **New** decisions file: one row per P7 item (116 rows). Columns: `item_id, text, review_source (lookalike_v4 / plain_scan_v4), review_item_no, recorded_decision, authorised_treatment (keep / exclude), reason, authorised_by, authorised_on`. 112 keep (13 Outside + 99 Clear), 4 exclude | `research_paper/experiments/pilot/authorised_review_treatments_v1.csv` |
| Builder reads **only** the decisions file for P7. It aborts if the file does not list every generated P7 item exactly once, or contradicts the review records: Outside/Clear must be `keep`; Uncertain/Flag for review must be `exclude`. Each exclusion is logged as `review_exclusion` with its reason | `lexeval/build_products.py` |
| Remove the old implicit path (`reviewed = any(...)`, `plain_exceptions`) from the build. Make every review-sheet writer refuse to overwrite an existing file, whatever its status. Add a function that validates the decisions file against the two review records | `lexeval/pilot.py` |
| Write the excluded items' full original rows, plus `exclusion_reason`, `decision_source` and `authorised_by`, to an audit file | build output: `research_paper/experiments/data/generated/excluded_items.csv` |
| Freeze guard: require the decisions file to be complete and consistent with the review records, and `excluded_items.csv` to match. No longer read the scan file's `REVIEWED` line | `run_all.py` |
| Never modified | `pilot/p7_lookalike_review_v4.csv`, `pilot/p7_plain_scan_progress_v4.csv`, `pilot/p7_plain_scan_v4.txt`, `pilot/pilot_review_sheet_v4.csv`, `pilot/pilot_reviewed_items.json` |

Tests for Phase A:
- **New** `tests/test_review_treatments.py`: completeness; consistency (Outside/Clear → keep, Uncertain/Flag → exclude); the builder aborts on a missing or contradictory row (synthetic temporary-directory fixture).
- After a temporary-directory build, the 4 IDs are absent from the scored rows and present in `excluded_items.csv`; the 13 + 99 retained items keep gold DECLINE.
- Original review and scan files are byte-identical before and after a build (hash test).
- No writer overwrites an existing sheet.
- Updated `tests/test_systems_and_data.py`: the determinism test compares against the *rebuilt* production files, so it only passes after Phase D.

### Phase B — Pilot evaluation-time exclusion
| Action | Files |
|---|---|
| **New** exclusions file. For each of the 8 items: ID, benchmark, split (`test`), category, reason ("inspected during labelling-rule pilot, 23 Nov 2026"), source `pilot/pilot_reviewed_items.json`. A separate `sensitivity_sibling_clusters` block is fixed *now*, before any TEST result (§6) | `research_paper/experiments/evaluation_exclusions_v1.json` |
| One choke point for TEST data: `load_test_items()` removes the excluded IDs before *every* TEST computation. That covers product, identification and tax-behaviour results, propagation classes, error and abstention counts, summaries, primary and ladder paired tests, and figures. It aborts if a listed ID is missing from the benchmark or is not in TEST. Excluded items are listed (unscored) in `<run>/excluded_from_test_metrics.csv` | `lexeval/evaluate.py` |
| Validation checks that the exclusion IDs exist and are in TEST | `lexeval/validate.py` |
| Freeze manifest records the SHA-256 of the exclusions file; evaluation aborts on mismatch | `run_all.py` |

Tests for Phase B (**new** `tests/test_eval_exclusions.py`, synthetic fixtures only, never the real TEST split):
- no excluded ID appears in any item-level row, summary count, propagation row, paired-test input or figure input;
- `n` in summaries equals TEST size minus exclusions;
- a stale or non-TEST exclusion ID aborts evaluation;
- a manifest hash mismatch aborts evaluation.

### Phase C — Evaluation and latency safeguards
| Action | Files |
|---|---|
| **Latency:** the default and only permitted split is `dev`. Requesting `test` raises an error. Product workload = all DEV product items (estimate: 270 after Phase A), each with a canonical table country. Country workload = all DEV country items (655), each with a canonical product. Each workload is timed **separately**: 200 warm-up calls, then 30 repetitions over the whole workload. Report per workload and system: median, p95, p99, mean, SD, throughput, and **run-to-run variability** (spread and 95 % bootstrap interval of the 30 repetition medians). Record the environment (CPU model, cores, memory, OS, Python and package versions) | `lexeval/latency.py`, `run_all.py`, `config.json` (`latency` block: replace `workload_items: 1000` with per-workload definitions) |
| **Tuning:** hard assertion that only `split == "dev"` rows reach `tune()`, plus an instrumented test | `lexeval/tuning.py` |
| **TEST lock:** each TEST evaluation gets an immutable run ID (UTC timestamp + short hash of the manifest, tuning record and exclusions file). Outputs go to `results/runs/<run_id>/` and are never overwritten. `results/test_runs.jsonl` is an append-only log. A second TEST run requires `--rerun-reason` and `--authorised-by`, and is logged. Evaluation requires the frozen manifest, matching hashes, the DEV tuning record (`tuning_dev.json`) and an explicit `--split test` | `run_all.py`, `lexeval/evaluate.py` |

Tests for Phase C (**new** `tests/test_split_safeguards.py`):
- latency refuses `test`;
- latency reports product and country separately, with repetition-level variability;
- tuning never receives TEST rows;
- a TEST run without a frozen manifest, tuning record or explicit split is refused;
- a second run without an authorised reason is refused;
- an earlier run directory is never modified.

Lock tests use temporary directories.

**Latency interpretation (for the paper):**
- Repeated timings of the same inputs are *not* independent research examples.
- Intervals describe **measurement variability on the specified machine and workload only**, not general performance uncertainty.
- Results are indicative (shared cloud VM).

### Phase D — Production rebuild and validation
These steps run only after Phases A–C pass their tests.
1. Record the pre-rebuild hashes (above).
2. `run_all.py --stage build`.
3. **Exact-difference check** (script):
   - the new product file equals the old one minus exactly the 4 authorised IDs, with all other rows byte-identical;
   - `excluded_items.csv` holds those 4 original rows with reasons;
   - the build log has exactly 4 `review_exclusion` entries;
   - country and malformed-input files are byte-identical (hashes unchanged).
4. `run_all.py --stage validate`. Must show: 0 errors; per-category counts equal to the verified estimates in §5; no group straddling DEV/TEST; no identical texts across splits; no new near-duplicates; all 8 evaluation-exclusion IDs present and in TEST.
5. Reproducibility:
   - rebuild in temporary directories under two `PYTHONHASHSEED` values, and in a fresh virtual environment from `requirements.txt`;
   - all hashes must be identical to the production rebuild.
6. Run the full unit test suite (`backend/tests` and `research_paper/experiments/tests`); all must pass.
7. Update the documentation:
   - `RESEARCH_STATE.md`;
   - `research_paper/IMPLEMENTATION_CHANGES.md`;
   - `research_paper/experiments/dataset_sampling_rationale.md`;
   - `research_paper/experiments/p7_review_sheet.md` (status only).
8. Present the freeze checklist (§9) for author approval. **No freeze without that approval.**

## 5. Expected counts (ESTIMATES until verified by the Phase D rebuild)
Derived on 24 Nov 2026 from the current benchmark files, the cluster definitions (`cluster` column) and the decisions above. These are not measured results.

**Benchmark after Phase A (rows):**
- product 809 → **805** (DEV 272 → 270, TEST 537 → 535);
- P7 116 → **112**: DEV 27 → 25 (21 plain + 4 look-alikes), TEST 89 → 87 (78 plain + 9 look-alikes);
- country 2,122 and malformed-input 18 unchanged.

**Scored TEST items and clusters after Phase A + Phase B** (format: items / clusters):

| Category | Now | After A | After A + B | Clusters lost |
|---|---|---|---|---|
| P1 | 76 / 38 | 76 / 38 | 76 / 38 | 0 |
| P2 | 76 / 38 | 76 / 38 | 75 / 38 | 0 (Scanner sibling remains) |
| P3 | 76 / 38 | 76 / 38 | 75 / 38 | 0 (Graphics Card sibling remains) |
| P4 | 16 / 16 | 16 / 16 | 15 / 15 | 1 |
| P5 | 22 / 12 | 22 / 12 | 22 / 12 | 0 |
| P6 | 11 / 11 | 11 / 11 | 10 / 10 | 1 |
| P7 | 89 / 89 | 87 / 87 | 86 / 86 | 3 (2 from A, 1 from B) |
| P8 | 171 / 171 | 171 / 171 | 170 / 170 | 1 |
| **Pooled P1–P7** | 366 / 138 | — | **359 / 134** | 4 |
| J1 | 81 / 27 | unchanged | 81 / 27 | 0 |
| J2 | 344 / 172 | unchanged | 344 / 172 | 0 |
| J3 | 272 / 168 | unchanged | 271 / 168 | **0** (DZ "name" remains in J3 TEST) |
| J4 | 170 / 170 | unchanged | 170 / 170 | 0 |
| J5 | 564 / 147 | unchanged | 564 / 147 | 0 |
| J6 | 10 / 10 | unchanged | 9 / 9 | 1 |
| J7 | 26 / 26 | unchanged | 26 / 26 | 0 |
| **Pooled held-out J4–J7** | 770 / 208 | — | **769 / 207** | 1 |

- **Correction:** the earlier plan said "only one cluster is lost, in J6". That holds for the country benchmark only. Product categories lose clusters in P4, P6, P7 and P8.
- **Totals scored after A + B:** product 529; country 1,465.
- **DEV latency workloads after A:** product 270; country 655.

## 6. Sibling sensitivity analysis (secondary; definition fixed now, before any TEST result)
- **Definition:** a sibling is a TEST item in the same benchmark sharing the `cluster` value of any of the 8 excluded items, after removing the 4 Phase A exclusions.
- **Product clusters:** `base:Scanner`, `base:Graphics Card`, `base:WiFi Adapter`, `P6_ambiguous|word|computer`, `P7_outside|card index`, `P8_hs|other_chapter|080122`. Estimated **18 sibling items**: P1 6, P2 5, P3 5, P5 2.
- **Country clusters:** `DZ`, `CE|sint`. Estimated **9 sibling items**: J2 2, J3 1, J4 1, J5 5.
- The cluster list will be written into `evaluation_exclusions_v1.json` before the freeze and hashed in the manifest.
- The analysis re-computes the primary pooled metrics and primary paired comparisons with siblings removed. It is reported separately, labelled as sensitivity, and never replaces the primary results.

## 7. Acceptance criteria and risks
**Acceptance criteria:**
- all new and existing unit tests pass;
- the Phase D exact-difference check passes;
- validation shows 0 errors and counts equal to §5 (any deviation must be explained before freezing);
- reproducibility hashes match;
- original review and scan files and the original application are byte-identical;
- `main` is untouched.

| Risk | Mitigation |
|---|---|
| Leakage via the 8 inspected TEST items | Single TEST choke point, stale-ID guard, hash in manifest, synthetic tests; sibling sensitivity analysis |
| Excluding valid examples | Only the 4 author-authorised exclusions are applied. Every exclusion is logged with reason and kept in full in `excluded_items.csv`. Counts are reported in the paper |
| Uncertain items silently kept | Builder aborts unless every Uncertain/Flag item is `exclude` in the decisions file |
| Overwriting original review files | Writers never overwrite; byte-identity tests |
| Accidental TEST use (tuning, latency, reruns) | DEV-only assertions, latency refuses TEST, TEST lock with immutable run IDs and an authorised-rerun log |
| Documentation drift | Phase D step 7. Stale passages are already listed in `RESEARCH_STATE.md` §15 |
| Statistical power | Pooled P1–P7 TEST 359 items / 134 clusters; look-alikes scored in TEST: 8 (9 − card index). Small categories (P4–P6, J6, J7, look-alikes) are reported descriptively only |
| Validity of the research question | Unchanged. Exclusions remove only ambiguous labels and inspected items, and the strict DEV tuning rule is untouched |

**Remaining uncertainties:**
- The estimates in §5 assume the rebuild changes nothing except the 4 exclusions. This must be confirmed by the exact-difference check.
- The new latency workload definition requires a `config.json` change, part of Phase C. It is approved in principle but not yet made.

## 8. Corrected execution order
1. **Phase A** code and tests (temporary-directory builds only).
2. **Phase B** code and tests (synthetic fixtures only).
3. **Phase C** code and tests.
4. Full unit-test run. **No production rebuild before steps 1–3 pass.**
5. **Phase D:** production rebuild, exact-difference check, validation, reproducibility checks, documentation.
6. Present the freeze checklist and wait for author approval.

**No TEST-set evaluation at any point in this plan.**

## 9. Conditions required before freezing
- [ ] Phases A–C implemented; all tests pass.
- [ ] Production rebuild done; exact-difference check passed (exactly 4 rows removed, all else identical).
- [ ] `excluded_items.csv` complete, with reasons.
- [ ] Validation 0 errors; counts reconciled with §5.
- [ ] `evaluation_exclusions_v1.json` complete (8 IDs + sibling clusters); IDs verified in TEST.
- [ ] Reproducibility (hash seeds + clean venv) passed.
- [ ] TEST lock, DEV-only tuning and DEV-only latency safeguards tested.
- [ ] Original review/scan files, original application and `main` unchanged.
- [ ] Documentation updated and consistent.
- [ ] **Explicit author approval to freeze.**

---

**Implementation of this plan has NOT been authorised.** Await explicit author authorisation before changing any code, configuration or data.
