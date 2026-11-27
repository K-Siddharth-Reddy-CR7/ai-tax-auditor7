# IMPLEMENTATION_PLAN.md — applying the review decisions and evaluation safeguards

**Status (27 Nov 2026): FROZEN; DEV STAGE COMPLETE. No TEST evaluation has been run.** DEV stage (S1 tuning, DEV evaluation of B/S0/S1, DEV figure, DEV latency): outputs committed in `b0248b7`, report `research_paper/dev_results_report.md`; selected S1 setting coverage 1.0, typo edits 1, minimum length 4. Joint approval by Authors 1 and 2 (`research_paper/freeze_approval_record.md`); freeze executed at `693cb28`; `MANIFEST.json` committed in `453fc55` (code identity `1930a0b2…`, 38 files). Phases A and B are accepted (audits of `ead53a4` and `f354cd7`). Phases C, C.1 and C.2 are accepted with conditions (audits of `d6c683e`, `c103cac` and `daffba1`; the C.2 conditions are documentation, recorded in `RESEARCH_STATE.md`).
- Phase D:
  - step 0 test correction (immutable original from `a0129b8`);
  - production rebuild (exactly 4 authorised exclusions);
  - validation (0 errors, 0 warnings; every count in §5 verified);
  - four byte-identical reproducibility builds.

  Details: `IMPLEMENTATION_CHANGES.md` §12.
- Phase C.2 (pre-freeze corrections D2–D5 from the C.1 audit) changed `lexeval/run_control.py`, `run_all.py` and the tests. Details: `IMPLEMENTATION_CHANGES.md` §11.
- Phase C.1 (corrections from the Phase C audit) changed `lexeval/run_control.py`, `tuning.py`, `figures.py`, `run_all.py` and the tests. Details: `IMPLEMENTATION_CHANGES.md` §10.
- Phase C added `lexeval/run_control.py` and changed `evaluate.py`, `tuning.py`, `latency.py`, `figures.py`, `eval_exclusions.py`, `run_all.py`, `config.json` (latency block) and tests. Details: `IMPLEMENTATION_CHANGES.md` §9.
- Phase A added the decisions file and changed `lexeval/pilot.py`, `lexeval/build_products.py`, `run_all.py` and tests. Details: `research_paper/IMPLEMENTATION_CHANGES.md` §7.
- Phase B added `evaluation_exclusions_v1.json` and the TEST choke point `lexeval/eval_exclusions.py`, and changed `lexeval/evaluate.py`, `lexeval/validate.py`, `run_all.py` and tests. Details: `IMPLEMENTATION_CHANGES.md` §8.
- The final deliverable now includes a complete IEEE conference manuscript (§10).
- No configuration, committed benchmark row, label, generated file, review record or scan file has been changed.
- Phase D rebuilt the benchmark (27 Nov 2026); the freeze and the DEV stage followed on 27 Nov 2026. Nothing has been evaluated on TEST.
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
- **Defects 1–3 were fixed in Phase A (24 Nov 2026).** `--stage build` is now the Phase D production rebuild and must not be run before Phase D is authorised. `--stage freeze` refuses until that rebuild exists.

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

## 3. Separate pilot evaluation exclusion (implemented in Phase B, 26 Nov 2026)
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
- Updated `tests/test_systems_and_data.py`: the determinism test compares against the *rebuilt* production files. **As implemented:** before Phase D it requires the committed draft minus exactly the 4 authorised rows (all other bytes identical); after Phase D, full byte-identity. It passes in both states and fails on partial application.

### Phase B — Pilot evaluation-time exclusion (IMPLEMENTED 26 Nov 2026)
**As implemented:**
- The exclusions file is `research_paper/experiments/evaluation_exclusions_v1.json`.
- The choke point is `lexeval/eval_exclusions.py::load_test_items`. It requires the manifest hash, validates, removes the 8 IDs, and returns an audit list.
- A second, independent guard (`assert_no_excluded`) runs inside every metric function and on the item-level rows.
- Sibling sensitivity outputs are written separately by `evaluate()` for the primary TEST evaluation.
- The audit file is `<tag>_test_excluded_from_metrics.csv` in `results/processed/` (the per-run directory comes with the Phase C TEST lock).
- Tests: 43 in `tests/test_eval_exclusions.py`.

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

### Phase C — Evaluation and latency safeguards (IMPLEMENTED 26 Nov 2026)
**As implemented** (details in `IMPLEMENTATION_CHANGES.md` §9):
- **Single TEST route:** `run_all.py --stage evaluate --split test --authorised-by NAME [--rerun-reason TEXT]`. `evaluate()` and `load()` take no hash and accept TEST only with an open run from `run_control.open_run`, which verifies every manifest hash.
- **Per-item guards:** `run_product_task` and `run_country_task` refuse excluded IDs always, refuse rows without split `dev`/`test`, and refuse TEST rows outside an open run.
- **Tuning:** DEV-only checks; the record is never overwritten. The selection rule is unchanged.
- **Latency:** DEV-only, with separate product and country workloads, run-to-run variability and no TEST fallback; it is a separate `--stage latency`.
- **Risk–coverage figure:** DEV only (author decision, 26 Nov 2026), drawn from the DEV tuning grid and the B/S0/S1 DEV evaluation by `--stage tune`. The TEST-grid version was removed.
- **TEST figures:** drawn inside the run from its own outputs, after split and exclusion checks.
- **Ladder:** the pairs helper `evaluate.ladder_pairs`, tested with and without sensitivity outputs.
- **Run controls:** permanent run IDs, `results/runs/<run_id>/`, a hash-chained append-only `results/test_runs.jsonl`, exclusive-create outputs made read-only at close, and logged aborted runs.

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

### Phase C.1 — Corrections from the Phase C audit (IMPLEMENTED 26 Nov 2026)
- **R1, reconciliation:** `run_control.reconcile` checks the log against `results/runs/` and `results/run_recoveries/` before every TEST run, and any inconsistency refuses the run.
  - **Recovery:** `--stage recover-runs --authorised-by NAME --recovery-reason TEXT` is allowed only when reconciliation fails. It deletes and rewrites nothing. It writes a recovery record (problems, current log hash and line count, digest of every run directory) and appends a `recovery` entry. A missing log is never regenerated; a new log starts with the recovery entry and the record states `log_missing: true`. Afterwards the acknowledged evidence must stay byte-identical, and the acknowledged runs count as earlier runs.
  - **Documented state:** an interrupted run (started, never closed) is allowed and counts as an earlier run.
- **R2, code identity:** `CODE_IDENTITY_PATTERNS` in `run_control.py` is the exact list:
  - the evaluation code (`run_all.py`, `lexeval/*.py`);
  - the system code (`backend/server.py`, `backend/lexitax_v2/*.py`);
  - the three requirements files;
  - the four original tables the systems read.

  Tests, documentation, results, `config.json` and `data/generated` (both hashed separately) and the frontend are excluded.
  - **At freeze:** a clean tree is required and the identity and commit are recorded.
  - **At TEST:** the identity must match, the tree must be clean, and HEAD must be the frozen commit or a descendant that changes no identity path. Exact commit equality is impossible, because `MANIFEST.json` itself must be committed after the freeze.
- **R3, provenance:** the tuning record is re-checked at load; the manifest is re-checked at close (a failure closes the run as aborted and raises); `run.json` records the Python and package versions.
- **Risk–coverage:** `tuning.full_pipeline_grid` runs all 49 grid settings through the full S1 pipeline on the DEV product inputs used by the DEV system evaluation. It records resolver-level scores, full-pipeline scores and their differences, plus the selected setting and its full-pipeline point. Selection is unchanged. The figure is titled "S1 full-pipeline risk–coverage across the tuning grid (DEV)".
- **Tie-breaks:** documented as described in `RESEARCH_STATE.md` §9 and recorded in the tuning record.
- **Phase C tests:** now state-aware, comparing before and after a test instead of requiring that no manifest exists.

### Phase C.2 — Pre-freeze corrections from the Phase C.1 audit (IMPLEMENTED 26 Nov 2026)
**D2, recovery protocol v2** (`run_control.recover`, `_recovery_plan`, `reconcile`):
- **Records:** every recovery writes one new, sequence-numbered record (schema `lexitax-run-recovery/2`) and appends one log entry. The record snapshots:
  - the exact log bytes;
  - a full file inventory with hashes for every run directory;
  - every earlier recovery record (present-verified, present-unverifiable or missing, with its hash and the sources of that hash);
  - runs known only from the log or from earlier records;
  - each run's log-entry status;
  - the problems found.
- **Reconciliation** binds the latest record to the last recovery entry in the log, and requires the latest record to list every earlier sequence number. It checks every present earlier record against its listed hash and every acknowledged run against its inventory.
- **Repeated loss of the log or of recovery entries is recoverable**, because the next record acknowledges the surviving earlier records.
- **Fails closed (writes nothing)** on unreadable records, duplicate sequence numbers, a record contradicted by a recorded hash, or unevidenced sequence gaps. The remedy is to restore the record from version control.
- **Never reconstructed:** no 'started' or 'completed' history is ever recreated.

**D3, close-time failures:** `close_run` treats any exception from the manifest check as a close-integrity failure (closed as aborted, evidence kept, original exception chained). `verify_manifest` reports an unreadable manifest as a `RunControlError`. `stage_evaluate` re-raises the original evaluation error with the close failure added as a note, and the close record holds both errors. Errors outside the verification boundary are not caught.

**D4, interrupted runs:** a recovery is also allowed (and required before any new TEST run) when an interrupted run is unacknowledged. The record keeps a SHA-256 inventory of every file present then; later modified, deleted or added files are detected. A repeated recovery records any change since the previous acknowledgement instead of hiding it. Recovery-time hashes do not establish integrity before the recovery.

**D5, nested modules:** the identity patterns are `lexeval/**/*.py` and `backend/lexitax_v2/**/*.py`. The same expansion is used for hashing (`glob(recursive=True)`) and for the commit-diff check (regex translation). Today's inventory is unchanged at 38 files.

### Phase D — Production rebuild and validation
These steps run only after Phases A–C pass their tests.
0. **Correction carried over from the Phase A audit (required before step 2).**
   - **Problem:** six Phase A tests in `tests/test_review_treatments.py` read the live `data/generated/product_benchmark.csv` as "the original pre-review draft":
     - `test_decisions_match_every_review_record_and_draft_item`
     - `test_build_equals_draft_minus_exactly_four_rows`
     - `test_audit_file_holds_full_original_rows_and_reasons`
     - `test_freeze_guard_refuses_current_pre_phase_d_draft`
     - `test_freeze_guard_refuses_draft_still_containing_exclusions`
     - `test_stage_freeze_refuses_without_writing_manifest`
     - plus, from the Phase B audit: `tests/test_eval_exclusions.py::test_protected_files_unchanged`, which pins the product benchmark hash `4b69c5bb…` that the rebuild changes on purpose
   - **Fix:** pin the original draft from git history at `a0129b8` (`git show a0129b8:research_paper/experiments/data/generated/product_benchmark.csv`). Verify its SHA-256 `4b69c5bb24ed519831490118e4d86ca2dfb38575cde4db5479c4e3feda1b5351` and make those tests use this immutable copy. Test both the pre-rebuild and post-rebuild states strictly.
   - **Optional, also from the audit:** a header check on `excluded_items.csv` in the freeze guard; and a post-rebuild byte comparison of the production `excluded_items.csv` in the determinism test.
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

## 5. Expected counts (VERIFIED by the Phase D rebuild, 27 Nov 2026)
Derived on 24 Nov 2026 from the benchmark files, the cluster definitions (`cluster` column) and the decisions above. On 27 Nov 2026 every figure below was checked against the rebuilt files: all row, split, category, cluster, pooled, sibling and latency-workload counts match exactly. These are benchmark counts, not measured results.

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

## 8. Overall project sequence (updated 26 Nov 2026)
Each step needs its own explicit authorisation.
1. **Phase A:** review treatments. **Completed and accepted** (`ead53a4`).
2. **Phase B:** evaluation exclusions. **Completed and accepted** (`f354cd7`).
3. **Phase C:** DEV-only latency and tuning, the single TEST route with permanent run controls, figure paths (DEV-only risk–coverage), ladder tests. **Conditionally accepted** (`d6c683e`).
3a. **Phase C.1:** run-log reconciliation and recovery, code identity at freeze, provenance re-checks, full-pipeline DEV grid, tie-break documentation, state-aware tests. **Conditionally accepted** (`c103cac`).
3b. **Phase C.2:** recovery protocol v2 (D2), close-time failure handling (D3), interrupted-run output protection (D4), nested-module code identity (D5). **Implemented and tested**; awaiting acceptance.
4. **Phase D:** the Phase A audit correction (step 0), production rebuild, exact-difference check, validation, reproducibility, documentation, freeze checklist. **Completed 27 Nov 2026.**
5. **Benchmark freeze:** **Completed 27 Nov 2026** (joint author approval; executed at `693cb28`; `MANIFEST.json` committed in `453fc55`).
6. **DEV tuning, then one TEST evaluation:** separate authorisations. **DEV stage completed 27 Nov 2026** (`b0248b7`; `research_paper/dev_results_report.md`). The TEST evaluation awaits authorisation.
7. **Experimental analysis and results audit.**
8. **Complete manuscript (§10, Stage 2) and final author review.**

The manuscript's Stage 1 (evidence-supported, results-independent sections, §10) may be prepared alongside steps 2–6 when authorised, without changing the engineering scope.

**No TEST-set evaluation before step 6.**

## 9. Conditions required before freezing
Status after Phase D (27 Nov 2026):
- [x] Phases A–C (with C.1 and C.2) implemented; all tests pass (276 experiment, 63 backend).
- [x] Production rebuild done; exact-difference check passed: exactly 4 rows removed, every other byte identical to the original from `a0129b8`, and country and malformed unchanged.
- [x] `excluded_items.csv` complete: the 4 full original rows, with reasons, decisions and authorisation.
- [x] Validation: 0 errors, 0 warnings; counts reconciled with §5.
- [x] `evaluation_exclusions_v1.json` valid against the rebuilt benchmark: 8 IDs, all in TEST, disjoint from the 4 review exclusions; sibling clusters fixed (18 product / 9 country items).
- [x] Reproducibility: four isolated builds (two environments, one fresh; `PYTHONHASHSEED` 0, 4242, 987654) byte-identical to production.
- [x] TEST lock, DEV-only tuning and DEV-only latency safeguards tested.
- [x] Original review and scan files and the original application unchanged; `main` unchanged.
- [x] Documentation updated (`RESEARCH_STATE.md`, this plan, `IMPLEMENTATION_CHANGES.md` §12, the experiment README and the dataset rationale/P7 sheet banners).
- [x] **Explicit author approval to freeze:** joint approval by Author 1 (Syeda Sayeeda Farhath) and Author 2 (Siddharth Karanam), 27 Nov 2026 (`research_paper/freeze_approval_record.md`, `693cb28`). Freeze executed on the clean tree at `693cb28`; `MANIFEST.json` (SHA-256 `0d7bddd9…`) committed in `453fc55` and verified against the approved hashes and code identity.

---

## 10. Final deliverable: IEEE conference manuscript (added 26 Nov 2026)
The required final deliverable is a complete, academically defensible IEEE conference paper. It is prepared progressively from verified project evidence and verified literature, so that the authors can check it and rewrite it in their own voice. The workspace is `research_paper/manuscript/`; see its `README.md` and `outline.md`.

**Working title:** "Silent Errors versus Safe Abstention in Staged Customs Pre-Assessment: An Empirical Study of Product and Jurisdiction Resolution". A more precise title may be proposed only once results exist. The research question is not to change.

**Stage 1: evidence-supported draft (may proceed during Phases B–D when authorised).**
- Sections: introduction and motivation, related work, research questions, system architecture, methodology, dataset construction, annotation protocol, evaluation design and metrics, limitations and threats to validity.
- Sources: committed code, configuration, schemas and documents, plus verified references only.
- Results-dependent statements are marked placeholders; unknown facts are marked for author confirmation.

**Stage 2: complete manuscript (only after the freeze and the separately authorised experiments have been completed and audited).**
- Populate results; generate tables and figures from the result files; report the specified statistics, the error-propagation analysis, the separate sibling sensitivity analysis, and latency with run-to-run variability.
- Write the abstract and conclusion from actual findings, and report negative or inconclusive results.

**Deliverables:**
1. LaTeX source using the selected IEEE conference template;
2. `.bib` bibliography;
3. publication-quality figures;
4. tables generated from result files;
5. literature evidence and verification table;
6. results-to-evidence traceability sheet;
7. author verification checklist;
8. unresolved methodological questions;
9. AI-use disclosure draft;
10. final PDF after the results are populated and formatting is checked.

**Rules:**
- **Accuracy:**
  - real, verified references only;
  - no invented results or capabilities; S1 is not to be described as better before the results show it;
  - the system is a fixed sequential six-stage Python pipeline with no LLM, and TF-IDF retrieval is a prototype, not generative RAG;
  - synthetic and prototype data, unofficial HS source, and no legal classification or compliance claims.
- **Authorship:** author order as in `RESEARCH_STATE.md` §12; no invented contributions or approvals; all authors approve the final version.
- **Venue:** the target conference, template and deadline are verified separately and must not be assumed.
- **AI disclosure:** it must accurately cover research planning, literature research, code, evaluation design, statistical-analysis assistance and manuscript drafting.

**Known constraint:** Crossref, OpenAlex, arXiv, DBLP and IEEE Xplore APIs were blocked by this environment's network policy (`literature_review.md` §1). Reference verification may need an allowlisted metadata host or author-exported BibTeX.

---

**Authorised so far: Phases A–D, the freeze and the DEV stage (all completed 27 Nov 2026).** Await explicit authorisation before the TEST evaluation, manuscript Stage 1 drafting, or any other step in §8.
