# RESEARCH_STATE.md — LEXITAX AUDIT research checkpoint

**Checkpoint date:** 24 Nov 2026.
**Written on branch:** `research/option-a-evaluation`, on top of commit `91b7305`. This file is committed as the next commit; run `git log -1` for its hash.
**Updated 27 Nov 2026: CURRENT STAGE = FROZEN; DEV STAGE AND THE SINGLE PLANNED TEST EVALUATION COMPLETE.** Phases A and B are accepted; Phases C, C.1 and C.2 are accepted with conditions (C.2 audit of `daffba1`); Phase D is complete. The results audit and manuscript each need separate authorisation. No further TEST run is planned; any rerun would need `--rerun-reason` and separate authorisation.
- **DEV stage (27 Nov 2026, authorised separately):** `run_all.py --stage tune` and `--stage latency` run once each at `ce6f98f` against the verified manifest; outputs committed unedited in `b0248b7`; report in `research_paper/dev_results_report.md`. Selected S1 setting (strict rule, feasible branch; all 49 settings feasible): `product_min_coverage=1.0`, `product_typo_max_edits=1`, `product_typo_min_len=4` (7 settings tied at DEV macro accuracy 1.000; chosen by the coverage tie-break; the coverage threshold had no effect on DEV). DEV results are in-sample for S1 and are not study results. No TEST item was loaded, scored or timed during the DEV stage.
- **TEST stage (27 Nov 2026, authorised separately):** single planned TEST run `20261127T104925Z-0f293784` (status completed; first and only run) through the authorised route at `0e34002`; outputs committed unedited in `e0bf964`; report `research_paper/test_results_report.md`. Primary (pooled) results: product P1–P7 S1 silent-error rate 0.000 (coverage 0.688, decision accuracy 0.997) vs S0 0.443 and B 0.053; held-out country identification J4–J7: no system identifies held-out forms (S1 and B abstain; S0 silent-error rate 0.016; no Holm-significant difference); tax behaviour J4–J7: B/S0 silent-error rates 1.000/0.996, S1 0.000 by refusal (137 over-refusals). 9 of 18 primary tests Holm-significant. No retuning or rerun.
- **Freeze (27 Nov 2026):** joint author approval by Author 1 (Syeda Sayeeda Farhath, corresponding author) and Author 2 (Siddharth Karanam), each given independently on 27 Nov 2026 for the package at `0e5a831` (`research_paper/freeze_approval_record.md`, committed in `693cb28`). `run_all.py --stage freeze` was executed at the documentation-only commit `693cb28` (`frozen_utc` 2026-11-27T09:35:27.652615+00:00). `MANIFEST.json` (SHA-256 `0d7bddd9c5c8a2855e79d8bfdaff1f81bcc272c2c7744d1c361ce3714ef0b19b`) was committed in `453fc55`. It pins code identity `1930a0b2b99eb6587879b9b330af93a7eb3d2a3df447dcc1e1c09b22fd44efb6` (38 files, git commit `693cb28`) and the seven approved hashes (§4; config `ba8b5ef7…`, review treatments `cc5f593f…`, evaluation exclusions `2ecacabe…`). `verify_manifest` passes. From now on any change to a pinned file or code-identity path invalidates the TEST evaluation.
- **Phase D:** the benchmark was rebuilt with exactly the four authorised P7 exclusions; validation shows 0 errors and 0 warnings; four isolated rebuilds are byte-identical. See §4 and `research_paper/IMPLEMENTATION_CHANGES.md` §12.
- **Original benchmark:** the pre-review product benchmark is preserved in git at `a0129b8` (SHA-256 `4b69c5bb24ed519831490118e4d86ca2dfb38575cde4db5479c4e3feda1b5351`, git blob `76a8e81c`). Tests read it only from there (`tests/_original.py`).
- **Phase C.2, D2 (recovery protocol v2):** recovery records form a sequence-numbered chain. Each recovery snapshots all surviving evidence and acknowledges every earlier record as present-verified, present-unverifiable or missing, so repeated loss of the log or of recovery entries stays recoverable. Recovery fails closed, writing nothing, on contradictory evidence: unreadable records, duplicate sequence numbers, a record whose bytes contradict a recorded hash, or unevidenced sequence gaps. No history is ever reconstructed.
- **Phase C.2, D3 (close-time failures):** any exception during the close-time manifest check closes the run as aborted, preserving the original exception. `stage_evaluate` keeps the evaluation error and adds the close failure as a note.
- **Phase C.2, D4 (interrupted runs):** a recovery acknowledges an interrupted run with a SHA-256 inventory of every file present; later changes are detected. A new TEST run is refused while an interrupted run is unacknowledged. The hashes do not establish integrity before the recovery.
- **Phase C.2, D5 (nested modules):** code identity now includes nested Python modules (`lexeval/**/*.py`, `backend/lexitax_v2/**/*.py`), using the same expansion for hashing and for the commit-diff check. See `IMPLEMENTATION_PLAN.md` (§8 overall sequence, §10 manuscript) and `research_paper/IMPLEMENTATION_CHANGES.md` §7–§10.
- **Phase C.1, run history (R1):** the TEST run log is reconciled against the run directories and recovery records before every TEST run. Inconsistencies block new runs until an authorised, evidence-preserving recovery (`--stage recover-runs`).
- **Phase C.1, code identity (R2):** the freeze pins a code identity hash and the git commit, and requires a clean working tree. A TEST run refuses changed code or a dirty tree.
- **Phase C.1, provenance (R3):** the tuning record is re-checked when loaded, and the manifest when a run closes; `run.json` records the Python and package versions.
- **Phase C.1, risk–coverage figure:** now drawn from a full-pipeline DEV grid. Selection is unchanged and resolver-level.
- Phase C: TEST evaluation runs only through `run_all.py --stage evaluate --split test --authorised-by NAME` inside a permanent, logged run (`lexeval/run_control.py`). Tuning and latency are DEV-only. The risk–coverage figure is DEV-only (author decision, 26 Nov 2026). No tuning, latency run, freeze or TEST evaluation has been performed.
- The eight-item pilot TEST exclusion is **implemented** (`research_paper/experiments/evaluation_exclusions_v1.json`, choke point `lexeval/eval_exclusions.py`). No evaluation has been run.
- The four P7 exclusions were authorised by the user and subsequently reviewed and approved by all four authors (user statement, 26 Nov 2026).
- The four P7 exclusions (§8) are recorded in the authoritative decisions file `research_paper/experiments/pilot/authorised_review_treatments_v1.csv` and enforced by the builder. They are **NOT yet applied to the committed benchmark files**; that is the Phase D production rebuild, not yet authorised.
- The last commit that changed generated benchmark data, generation code or configuration is **`a0129b8`** (verified in git history).

**Purpose:** a self-contained handoff so a fresh session can continue the research without this conversation. Every number below was verified against repository files at the time of writing, unless it is marked **[UNVERIFIED]**.

---

## ⚠️ 0. NON-NEGOTIABLE RESEARCH INTEGRITY RULES (read first)
1. **Never tune on the TEST split.** S1 parameter selection uses DEV only (`lexeval/tuning.py` filters `split == "dev"`).
2. **Never use TEST results for any development, design or model-selection decision.** TEST is used once, after the freeze, for the final evaluation.
3. **The 8 pilot-reviewed TEST items must be excluded from final TEST metrics** (§5). **Implemented in Phase B:** TEST rows are obtained only through `lexeval/eval_exclusions.load_test_items()`, which requires the exclusion-file hash from the freeze manifest. Every metric function also rejects rows with an excluded ID.
4. **Every exclusion must be documented with its reason and count**, and reported in the paper.
5. **Uncertain items must never be silently treated as accepted examples.** The 3 look-alikes marked Uncertain and the 1 plain name marked "Flag for review" (§6–§8) may not be kept as gold DECLINE items without explicit author authorisation.
6. **Never invent results, metrics, statistical significance or experimental outcomes.** No experiment has been run (§13).
7. **Never claim capabilities that are not implemented.** No LLM, no generative RAG, no multi-agent autonomy, no valuation-discrepancy detector, no risk scorer, no consensus auditor, no fraud detection, no legal classification.
8. **Preserve the original baseline and application.** `backend/server.py` and the original datasets must stay byte-identical to `main` (enforced by `backend/tests/test_original_untouched.py`).
9. **Do not modify `main`.** Do not merge. Do not force-push.
10. **Do not apply manual review decisions, change benchmark labels, remove examples, or rebuild the benchmark without explicit user authorisation.** Since Phase A, `run_all.py --stage build` applies exactly the 4 exclusions in `pilot/authorised_review_treatments_v1.csv` and writes `excluded_items.csv`. It is the Phase D production rebuild and must not be run until Phase D is authorised. `--stage pilot` can no longer overwrite any existing review file.
11. **Do not start experiments** (tune or evaluate) until the benchmark integrity review is complete and the user authorises the next stage.
12. **All experiments must be reproducible:** fixed seed, pinned dependencies, frozen and hashed data (`MANIFEST.json`), with configurations and raw and processed outputs preserved in `research_paper/experiments/results/`.

---

## 1. Project identity, question, objectives, contribution
- **Project:** LEXITAX AUDIT, an assistive customs and trade pre-assessment application (Flask backend, React/Vite/Three.js frontend). It identifies the product (→ HS-6 code via a catalogue), resolves the destination jurisdiction, applies duty and VAT/GST rates, computes landed cost, and attaches a policy record.
- **Repository:** `https://github.com/K-Siddharth-Reddy-CR7/ai-tax-auditor7` (canonical remote, confirmed by the authors).
- **Scope:** Option A, approved by the authors. A narrow empirical evaluation of the existing staged system. It does *not* implement the README's aspirational six-agent design.
- **Working title (provisional):** *"Silent Errors versus Safe Abstention in Staged Customs Pre-Assessment: An Empirical Study of Product and Jurisdiction Resolution."* To be refined after the literature review.
- **Primary research question:** How do product-identification and destination-country-resolution approaches trade off coverage against silent (unflagged) errors, and how do those errors propagate into downstream duty, VAT and landed-cost outputs?
- **Supporting questions** (`research_paper/research_question_and_scope.md`):
  - SQ1: product resolution;
  - SQ2: country identification versus tax-data availability;
  - SQ3: error propagation;
  - SQ4: latency and throughput;
  - SQ5: attribution via single-change ablation.
- **Intended contributions** (to be claimed only if results support them):
  1. a reproducible benchmark with labels independent of the systems;
  2. a three-system comparison with clustered statistics;
  3. an error-propagation analysis;
  4. the corrected pipeline S1.
- **Assistive only:** the system makes no legally authoritative customs determination.

## 2. Architecture and the three systems compared
| System | Code | Behaviour |
|---|---|---|
| **B**: original single-step baseline (unchanged) | `backend/server.py::run_normal_auditor_pipeline` | Substring product match (else HS "N/A"); exact country match (else silent default 5 % duty / 10 % VAT, USD); same landed-cost formula; no policy lookup |
| **S0**: original six-stage pipeline (unchanged) | `backend/server.py::run_agentic_auditor_pipeline` | Stages `input_agent` → `product_agent` → `rag_policy_agent` → `tax_agent` → `calculation_agent` → `report_agent`. Plain sequential Python functions sharing a dict; no LLM. Details below |
| **S1**: corrected six-stage pipeline (new) | `backend/lexitax_v2/` (config, normalize, legacy, reference, jurisdiction, product, validation, pipeline) | Trace stages: validation → jurisdiction → product → tax_lookup → calculation → policy_lookup. Reuses the *original* tables, `calculation_agent` and `PolicyRetriever` through a read-only loader (`legacy.py`). Details below |

S0's known silent failure modes:
- fabricated HS `8471.30` for unknown products;
- bidirectional substring country matching (e.g. "US" → Australia);
- silent default rates;
- FX rate 1.0 for missing currencies.

S1's behaviour:
- **Validation:** explicit input rejection.
- **Country identification:** ISO 3166-1 alias table (pycountry), kept separate from tax-data availability. Unsupported or unresolved destinations are refused, never defaulted.
- **Product resolution, by deterministic evidence tiers:**
  - T1: exact name;
  - T2: whole-word containment, with maximality, HS-uniqueness and an evidence-coverage threshold;
  - T3: bounded-typo containment.

  Otherwise S1 abstains. **No numerical confidence score**: the original code has none to calibrate.
- **Missing FX:** reported as unavailable (`null`), not replaced by 1.0.
- **Costs:** not computed for an unresolved product.

Other facts:
- **S1 provisional defaults** (`backend/lexitax_v2/config.py`): `product_min_coverage=0.5`, `product_typo_max_edits=1`, `product_typo_min_len=5`, `country_typo_max_edits=0`, `require_product_for_costs=True`. Final values must come from DEV tuning (§9).
- **Attribution ladder** (`lexeval/systems.py`), one change per step:
  - L0 = S0;
  - L1 + validation;
  - L2 + ISO identification (defaults retained; also changes the policy-query string);
  - L3 + refusal without tax data and no FX substitution;
  - L4 + product abstention (no fabricated HS; costs gated on product);
  - L5 = S1.

  L0 ≡ S0 and L5 ≡ S1 were verified in the smoke stage on the 400 canonical transactions and in tests on DEV samples.
- **Extra ablations:** S0 − word-overlap tier; S0 − partial country match; S1 − coverage guard; S1 − typo tier; S1 + country typo.
- **Original data (unchanged, synthetic):**
  - `products.json` 1,200 (60 base types × 20 name variants, 43 HS-6 codes);
  - `taxes.json` 40 countries (unsourced rates);
  - `trade_policies.json` 240 (identical placeholder text);
  - `sample_transactions.json` 400 (arithmetic sequences).
- **Application changes on this branch:**
  - C1 (S1 package + tests), approved;
  - C3 (frontend text corrections removing hard-coded "0 % false negatives / 37.5 % / 100 %" and other inaccurate claims; 4 files), approved;
  - C2 (`/api/v2/audit`) **deferred**;
  - README unchanged; it still lists 3 authors (§12).

## 3. Methodology and experimental design
Authoritative documents, newest first:
- `research_paper/phase8_pilot_record_and_integrity.md`;
- `research_paper/phase7_methodology_decisions.md`;
- `research_paper/experiments/dataset_sampling_rationale.md` (v4 banner);
- `research_paper/experiments/data_provenance.md` (v4);
- `research_paper/pre_evaluation_methodology_audit.md`;
- `research_paper/experimental_evaluation_plan.md` (v2 body, plus v3/v4 amendment banners).

Design:
- **Label independence:** labels come only from reference data (HS 2022 mirror, ISO 3166-1, CLDR 47, Unicode emoji names), the catalogue (identity), or pre-declared rules. Never from system outputs.
- **Separate evaluations:** product (HS-6 / catalogue type) with the country fixed to a canonical table name; country identification (gold ISO); tax-data behaviour (compute vs refuse); malformed-input rejection (18 items).
- **Propagation:** two controlled runs, varying only the product or only the country. Outcome classes: no error, masked, financial error (flagged or silent), computed-when-should-refuse, over-refusal, explicit refusal.
- **Outcome taxonomy** (`lexeval/scoring.py`): CORRECT, SAFE_ABSTENTION, OVER_ABSTENTION, EXPLICIT_FAILURE, SILENT_ERROR. "Safe" = not a silent error. The EITHER outcome was **removed** in Phase 7.
- **Country gold vs system behaviour:** `gold_iso` / `gold_tax_action` are gold fields. Result rows record `system_iso` and safety flags. A valid alias that a system does not know, followed by abstention, scores OVER_ABSTENTION, never CORRECT.
- **Pooled scope:**
  - pooled product claims use P1–P7 (P8 is reported separately);
  - pooled country claims use held-out forms J4–J7 only (J1–J3 are in S1's own table, so solved by construction).

## 4. Benchmark: composition and splits (REBUILT and FROZEN 27 Nov 2026)
Files are in `research_paper/experiments/data/generated/`. They are deterministic (seed 20261114). The Phase D rebuild was reproduced byte-identically in four isolated builds: two virtual environments (one freshly created from `requirements.txt`) and `PYTHONHASHSEED` values 0, 4242 and 987654.

| File | SHA-256 (after the Phase D rebuild) |
|---|---|
| `product_benchmark.csv` | `a6a87fc3f7057a74eebd9d5b7809809820b892e4ac3b791fe1f4dc64c5935160` (the original `4b69c5bb…` minus exactly the 4 authorised rows) |
| `country_benchmark.csv` | `1bf3f48940c27b4ba7fad332bc8e0bbc367df1381a251e6345a3a6609444c929` (unchanged) |
| `malformed_inputs.csv` | `bb3af78811f382e8f1bcab7d622cfbe0737177a7a4644e8724b0258ef19655df` (unchanged) |
| `excluded_items.csv` | `fcdc6789fbb455b78c3f0f5229ba9eacdde111b42dadf61f7283e6b2717f44d1` (new: the 4 full original rows plus reasons) |
| `build_log.json` | `ac17b5fcc9ed11238d2322d0fc4e12caff8644edfd4d7aeed3a72f02870877bb` |
| `VALIDATION_REPORT.md` | `bb2abb9bccc00f7e3f9e099e2b42ce9322b08b64af38c0ad0259ef37e5a24155` |

**After the rebuild:** product **805 rows (DEV 270 / TEST 535)**; P7 **112** (DEV 25 = 21 plain + 4 look-alikes; TEST 87 = 78 + 9). The P7 rows in the tables below are the pre-rebuild values; the scored TEST counts are in `IMPLEMENTATION_PLAN.md` §5, now verified.

- `VALIDATION_REPORT.md`: 0 errors, 0 warnings.
- Split: group-level hash, **DEV 30 % / TEST 70 %**. Groups never straddle splits. DEV is used only for tuning. There is **no separate training split**: nothing is trained.

**Products (pre-rebuild original, 809 items, DEV 272 / TEST 537; after the rebuild 805, DEV 270 / TEST 535)**
| Category | Total | DEV | TEST | TEST clusters | Gold |
|---|---|---|---|---|---|
| P1 exact catalogue names | 120 | 44 | 76 | 38 | ANSWER |
| P2 formatting variants | 120 | 44 | 76 | 38 | ANSWER |
| P3 typos (2 per type) | 120 | 44 | 76 | 38 | ANSWER |
| P4 underspecified short forms (qualifier removed) | 30 | 14 | 16 | 16 | DECLINE |
| P5 confusable neighbours | 43 | 21 | 22 | 12 | ANSWER |
| P6 ambiguous words / category names | 17 | 6 | 11 | 11 | DECLINE |
| P7 outside catalogue (Unicode emoji names) | 116 (100 plain + 16 look-alikes) | 27 (21 + 6) | 89 (79 + 10) | 89 | DECLINE |
| P8 formal HS 2022 texts (separate category) | 243 | 72 | 171 | 171 | 43 ANSWER (in-catalogue codes) + 200 DECLINE |

P8 splits by kind:
- in-catalogue codes: 19 DEV / 24 TEST;
- near-domain unsupported: 22 / 78;
- other chapters: 31 / 69.

**Countries: 2,122 items (DEV 655 / TEST 1,467)**
| Category | Total | DEV | TEST | TEST clusters | In S1's table | Tax data available |
|---|---|---|---|---|---|---|
| J1 table names + noise | 120 | 39 | 81 | 27 | all | 120 |
| J2 ISO alpha-2/3 codes | 498 | 154 | 344 | 172 | all | 80 |
| J3 ISO names | 386 | 114 | 272 | 168 | all | 35 |
| J4 typos | 247 | 77 | 170 | 170 | none | 40 |
| J5 CLDR 47 localised names (held out) | 821 | 257 | 564 | 147 | none | 167 |
| J6 ambiguous words (no country) | 16 | 6 | 10 | 10 | none | 0 |
| J7 CLDR region names (no country) | 34 | 8 | 26 | 26 | none | 0 |

**Malformed inputs:** 18 (not split; expected rejection).

## 5. Pilot review (completed)
- **Reviewer:** Author 1 (Syeda Sayeeda Farhath), sole reviewer.
- **Result:** 10/10 Accept, no comments. Time spent not reported.
- **Recorded in:** `experiments/pilot/pilot_review_sheet_v4.csv`, `experiments/pilot/pilot_reviewed_items.json` (transcribed by the AI assistant from Author 1's message on 23 Nov 2026), and `experiments/pilot_review_sheet.md`. No inter-annotator agreement is claimed.
- **Outcome:** labelling rules accepted, with no rule changes.

| Pilot | Item ID | Split | Must be excluded from final TEST metrics? |
|---|---|---|---|
| P01 | `P2_format\|Scanner\|ws_punct` | test | **Yes** |
| P02 | `P3_typo\|Graphics Card\|typo\|0` | test | **Yes** |
| P03 | `P4_short\|WiFi Adapter\|head_noun` | test | **Yes** |
| P04 | `P5_confusable\|Memory Card\|typo_distinguishing_word` | dev | No (DEV) |
| P05 | `P6_ambiguous\|word\|computer` | test | **Yes** |
| P06 | `P7_outside\|card index` | test | **Yes** |
| P07 | `P8_hs\|other_chapter\|080122` | test | **Yes** |
| P08 | `CD\|NZ\|es` | dev | No (DEV) |
| P09 | `CB\|DZ\|official_name` | test | **Yes** |
| P10 | `CE\|sint` | test | **Yes** |

**Status of the exclusion:**
- Proposed method ("Option A", `phase8_pilot_record_and_integrity.md`): an evaluation-time exclusion list read from `pilot_reviewed_items.json`. Labels and splits are unchanged; the list is hashed in the freeze manifest; the inspected items are reported separately; a cluster-level sensitivity analysis is added.
- **Implemented (Phase B, 26 Nov 2026):** `evaluation_exclusions_v1.json` lists the 8 items, validated against `pilot_reviewed_items.json`, `pilot_review_sheet_v4.csv` and the benchmark. Its SHA-256 goes into the freeze manifest. The sibling clusters for the sensitivity analysis are fixed in the same file.

## 6. P7 look-alike review (completed): 16 decisions
Source: `experiments/pilot/p7_lookalike_review_v4.csv`. Reviewer: Author 1. No comments on any item.

| # | Item | Split | Decision |
|---|---|---|---|
| 1 | card file box | test | Outside |
| 2 | card index | test | Outside (also pilot P06) |
| 3 | card index dividers | test | Outside |
| 4 | **couch and lamp** | dev | **Uncertain** |
| 5 | credit card | test | Outside |
| 6 | cricket game | dev | Outside |
| 7 | flower playing cards | test | Outside |
| 8 | folding hand fan | test | Outside |
| 9 | game die | test | Outside |
| 10 | hair pick | dev | Outside |
| 11 | mouse trap | test | Outside |
| 12 | musical keyboard | test | Outside |
| 13 | slot machine | dev | Outside |
| 14 | **toothbrush** | test | **Uncertain** |
| 15 | **video game** | dev | **Uncertain** |
| 16 | water pistol | dev | Outside |

**Totals:** 13 Outside, 0 Potentially in catalogue, 3 Uncertain.

## 7. P7 plain-name scan (completed): 100 names
- **Records:** `experiments/pilot/p7_plain_scan_progress_v4.csv`, reviewer Author 1. The 100 names match `p7_plain_scan_v4.txt` exactly and in order.
- **Totals:** **99 Clear, 1 Flag for review, 0 pending.** The flagged item is **#81 `satellite antenna`** (TEST split, plain name, current gold DECLINE). No comments.
- The scan file `p7_plain_scan_v4.txt` itself is **unchanged**: still `REVIEWED: no` with an empty `EXCEPTIONS:` list. The progress CSV is a separate record that the benchmark builder does not read.

## 8. Treatment rules: recorded vs authorised vs applied
| Matter | Recorded decision | Pre-declared rule | Authorised to apply? | Applied? |
|---|---|---|---|---|
| Pilot (10 items) | 10 Accept | ≥ 9 Accept → rules accepted | n/a (no data change) | Yes (documentation only) |
| 8 pilot items in TEST | Inspected | Exclude from every final TEST metric via `evaluation_exclusions_v1.json`; rows preserved (`IMPLEMENTATION_PLAN.md` Phase B) | **Yes** (Phase B authorised 26 Nov 2026) | **Implemented in code**; applied at evaluation time (no evaluation run yet) |
| 13 Outside look-alikes | Outside | Keep as gold DECLINE | **No** | No (they are already in the draft as DECLINE) |
| 3 Uncertain look-alikes (couch and lamp, toothbrush, video game) | Uncertain | Exclude; full rows kept in an audit file | **Yes: approved by the user on 24 Nov 2026** | **Applied** in the Phase D rebuild (27 Nov 2026); full rows in `excluded_items.csv` |
| #81 satellite antenna | Flag for review | **Author decision (24 Nov 2026): exclude as Uncertain.** The current code has no mapping for "Flag for review"; Phase A adds one via the decisions file, without editing the scan file | **Yes: approved** | **Applied** in the Phase D rebuild; full row in `excluded_items.csv`. The scan file is not edited |
| 99 Clear plain names | Clear | Keep as gold DECLINE | No | No change needed |
| Freeze | Joint approval, Authors 1 and 2 (27 Nov 2026; `freeze_approval_record.md`) | Since Phase A, `run_all.py --stage freeze` refuses unless the decisions file validates against the review records and the benchmark, `excluded_items.csv` and `build_log.json` reflect exactly that file. The scan file's `REVIEWED` line is not read | **Yes** (27 Nov 2026) | **Yes**: executed at `693cb28`; `MANIFEST.json` committed in `453fc55` |

Projected sizes (estimates until the Phase D rebuild verifies them; full table with cluster counts in `IMPLEMENTATION_PLAN.md` §5):
- P7 total: 116 − 4 authorised exclusions = 112.
- P7 TEST: 89 − toothbrush = 88; − #81 = 87; − pilot "card index" = **86 scored**.
- Pilot exclusion alone changes TEST sizes as follows:

| Category | Before | After |
|---|---|---|
| P2 | 76 | 75 |
| P3 | 76 | 75 |
| P4 | 16 | 15 |
| P6 | 11 | 10 |
| P7 | 89 | 88 |
| P8 | 171 | 170 |
| J3 | 272 | 271 |
| J6 | 10 | 9 |

## 9. Test-set integrity and tuning rule
- **Strict DEV-only tuning rule** (author decision 15 Nov 2026; `config.json` `tuning_rule`; **must not be relaxed after seeing results**):
  - maximise DEV macro decision-accuracy over P2–P7, subject to DEV macro silent-error rate ≤ that of B on DEV;
  - if no setting satisfies this, **report so honestly** and pick the minimum-SER setting;
  - ties go to the larger coverage threshold, fewer typo edits, longer minimum length.
- Grid: coverage {0, .25, .34, .5, .67, .75, 1} × typo edits {0, 1, 2} × minimum length {4, 5, 6}.
- **No system has been run on TEST benchmark items.** Runs so far: the 400 canonical transactions (smoke), unit-test examples, and DEV-only dry runs in tests.
- `tune`, `latency` and `evaluate` are blocked until `data/generated/MANIFEST.json` exists and every hash in it verifies. The manifest exists since the freeze of 27 Nov 2026 and verifies; each stage still needs its own authorisation.
- **Tie-breaks (clarified in Phase C.1; the existing deterministic behaviour, not a rule change):**
  - feasible case: highest DEV macro decision accuracy, then larger coverage threshold, fewer typo edits, longer minimum length;
  - no feasible setting: lowest DEV macro silent-error rate; if tied, higher DEV macro decision accuracy; then the same three tie-breaks.
- **Grid size:** the configured grid has **49** settings, 7 × (1 + 2 × 3), because minimum length is irrelevant without typo edits. The Phase C audit report's "61" was a miscount.
- **Phase C (26 Nov 2026):**
  - `tune()` accepts only rows with split `dev`; anything else raises `TuningSplitError`. The tuning record (`results/tuning_dev.json`, split `dev`) is never overwritten.
  - `latency.measure` is DEV-only, refuses `test`, and has no fallback.
  - TEST rows can be scored only inside an authorised run.
- Fuzzy-matching baseline: **deferred** until initial results (author decision).

## 10. Statistical requirements (`config.json` → `statistics`; `lexeval/stats.py`, `evaluate.py`)
- **Primary CIs:** cluster bootstrap (resample clusters; 95 % percentile). Item-level Wilson intervals are secondary.
- **Primary paired tests:** cluster-level two-sided sign-flip permutation test (10,000 permutations; exact if ≤ 16 non-zero clusters) with a cluster-bootstrap CI for the difference. **Holm** correction across the primary family of 18 tests: (B–S0, S0–S1, B–S1) × (decision-correct, silent-error) × (product, identification, tax behaviour).
- **Secondary:** exact McNemar (item-level). Ladder comparisons form a separate, exploratory family.
- **Small categories** (P4, P5, P6, J6, J7) are reported descriptively; no per-category significance claims.
- **Latency (Phase C, `--stage latency`):** DEV only, never TEST.
  - **What is timed:** the systems' own entry points (`latency.raw_systems`), not the evaluation adapters.
  - **Workloads:** all DEV product items (about 270 after the rebuild) and all DEV country items (655), timed separately.
  - **Method:** 200 warm-up calls, then 30 repetitions of each whole workload, timed with `perf_counter_ns`.
  - **Reported per workload and system:** median, p95, p99, mean, SD, throughput, and run-to-run variability (repetition medians, min/max, IQR, and a bootstrap interval of their median), with the environment recorded.
  - **Interpretation:** repetitions are not independent examples. Results are indicative for a shared VM.
- No significance claims beyond these tests.

## 11. Data-source and claim limitations
- **HS 2022 data:** an unofficial GitHub mirror `datasets/harmonized-system` @ `b1be3f2` (UN Comtrade-derived, ODC-PDDL, abridged text, **not WCO legal text**).
  - Edition markers verified.
  - 9 duplicated-description codes and the placeholder are excluded.
  - Upstream verification is blocked in this environment.
  - **No legal-classification validation may be claimed.**
- **ISO 3166-1:** pycountry 26.2.16 (open re-publication). **CLDR 47:** Babel 2.18.0.
- **P7 names:** Unicode `emoji-test.txt` 16.0 (`unicode-org/unicodetools` @ `ccc86e5`, Unicode License v3; notice in `data/external/UNICODE_LICENSE_V3.txt`). These are not invoice lines.
- **Open Products Facts:** **withdrawn** (licence not established); none of its text is used.
- **Catalogue HS assignments are unverified**; some are debatable (e.g. Tablet, VR Headset, Graphics/Sound Card).
- **Synthetic data:** the catalogue, transactions and perturbations (typos, formatting, short forms) are synthetic. Tax rates are unsourced (EU rates are internally inconsistent), so financial correctness is relative to the project's own table only. Policy records are placeholders, so retrieval relevance is **not** evaluated.
- **Claims:** no claims about real-world customs compliance, real declarations, fraud, legal determinations, or generalisation beyond 60 product types and 40 jurisdictions.
- Same-team design of system and benchmark (AI-assisted) must be disclosed as a threat to validity.

## 12. Authorship and AI-use disclosure
Authors, in exact order (all: Dept. of CSE, Vardhaman College of Engineering, Hyderabad, India):

| # | Author | Email | Note |
|---|---|---|---|
| 1 | Syeda Sayeeda Farhath | syedasayeedafarhath@ieee.org | **Corresponding author (confirmed)** |
| 2 | Siddharth Karanam | siddharthreddy1908@gmail.com | |
| 3 | P. Naga Bhargav Reddy | nagabhargavreddy175@gmail.com | |
| 4 | Baalne Anjali | anjali1820@vardhaman.org | Faculty mentor. Authorship **conditional** on substantive manuscript review/revision and final approval |

- **External funding:** none (confirmed). No funding acknowledgement.
- **Do not invent CRediT contributions.** Known roles: A1 lead and coordination; A2 implementation; A3 literature survey; A4 guidance.
- **README discrepancy:** the README lists three students (K. Siddharth Reddy, Syeda Sayeeda Farhath, P. Naga Bhargav). The authors stated these are the same people as Authors 1–3. The README is intentionally unchanged.
- **AI disclosure (IEEE requirement; exact wording to be verified against current IEEE and venue policy):** an AI assistant was used for:
  - repository analysis;
  - writing S1 and the evaluation code;
  - designing the benchmark-generator rules;
  - drafting documentation;
  - screening suggestions;
  - transcribing human review decisions.

  The authors must verify all scientific content. No AI system may be listed as an author.

## 13. Phases: completed, pending, next actions
**Completed:**
- **Phase 1:** repository investigation (`repository_investigation.md`).
- **Phases 2–3:** scoping, protocol.
- **Phase 4:** S1, tests, C3.
- **Phase 5 infrastructure:** builders, scoring, statistics, ladder, latency, figures code.
- **Phase 6:** methodology audit and redesign.
- **Phase 7:** licence-clean P7, single-gold P4, gold/system separation, review materials.
- **Phase 8:** pilot record and integrity plan.
- **Manual reviews:** look-alike (16) and plain scan (100) complete.

**Not done:**
- literature review (strategy only, `literature_review.md`; no reference verified);
- conference shortlist (unverified leads only, `conference_shortlist.md`);
- results audit (the freeze, the DEV stage and the single TEST run were completed on 27 Nov 2026);
- figures and results;
- manuscript (no draft exists);
- final submission checklist;
- one comprehensive PR to `main` (to be opened only after stable results; left unmerged).

**Current stage (27 Nov 2026):** frozen (`MANIFEST.json` committed in `453fc55`); DEV stage complete (`b0248b7`, `research_paper/dev_results_report.md`); single TEST run `20261127T104925Z-0f293784` complete (`e0bf964`, `research_paper/test_results_report.md`; experiment tests 276/276 and backend 63/63 pass with all outputs present). The results audit and manuscript drafting each await explicit authorisation (`IMPLEMENTATION_PLAN.md` §8).

**Clarifications from the Phase C.2 audit (limits of the recovery evidence; no code was changed in Phase D):**
- **Acknowledged is not verified.** A recovery record acknowledges evidence as found; it does not verify it.
  - "present_verified" means only that the record's bytes match a hash recorded by another surviving record or a log line.
  - When the only such source is itself unconfirmable (for example after a log loss, the newest record has no surviving log line), the whole chain rests on unconfirmable evidence, even where earlier records are labelled verified. `hash_sources` names the source.
- **Unverified log lines prove nothing.** A run ID found only in an unverified part of the log (for example a line after a broken hash link) is recorded by a recovery as "evidence: log 'started' entry" and stays in the run history. It is not independently verified, and must not be described as a verified run.
- **Conflicts are not attributions.** When recovery hashes conflict, the current refusal message says the earlier record "was modified". Either the earlier record or the record that claims its hash may have been altered; treat it as a conflict between the named sources. A wording change needs a separately authorised code change.
- **No concurrency.** Concurrent TEST runs and recovery operations are not permitted. There is no inter-process lock, and a recovery run while another process has a TEST run open would acknowledge that run mid-way.
- **Interrupted runs:** their outputs are protected only from the recovery-time inventory onward; nothing establishes their integrity before that.
- **Closing failures:** if `close_run` fails outside its verification step (an internal error), `close.json` may exist without a closing log line. That state is refused until a recovery.
- **Dot-folders:** a module inside a dot-folder under `lexeval/` or `lexitax_v2/` is matched by the commit check but not by the content hash. Such folders cannot be imported as packages.
- **Local evidence only:** local hash chains give no protection against a determined rewrite of all local evidence; git commits and the authors' records are the external check. The final deliverable includes a complete IEEE manuscript (`IMPLEMENTATION_PLAN.md` §10; workspace `research_paper/manuscript/`).

**Meaning of acknowledged history (Phase C.2):** a recovery record acknowledges evidence as found. It:
- distinguishes runs whose log entries survive from runs whose entries are missing;
- lists runs known only from the log or from earlier records;
- marks earlier records as present-verified (an independent hash agrees), present-unverifiable (no surviving independent hash) or missing.

It never restores missing entries, and it never vouches for content that can no longer be checked.

**TEST run-log limits (stated honestly):**
- The hash chain has no secret key. Anyone who can rewrite all local evidence consistently (log, run directories, recovery records) can produce an undetectable history, and deleting all evidence is undetectable locally.
- The controls detect accidental and casual changes; they are not cryptographic proof. Git history and the authors' records are the external check.

**Post-freeze workflow implied by R2:**
1. Freeze on a clean, committed tree.
2. Commit `MANIFEST.json`, and later the DEV tuning, figure and latency outputs, before the TEST run. The tree must be clean, and later commits may not touch code-identity paths.
3. After a TEST run, commit its outputs before any authorised rerun.

Author decisions of 24 Nov 2026 on the eight design questions (detail in `IMPLEMENTATION_PLAN.md` §1):
1. single decisions file;
2. remove exclusions from scoring, keeping an audit file;
3. dedicated `evaluation_exclusions_v1.json`;
4. P04/P08 stay in DEV;
5. pre-defined sibling sensitivity analysis;
6. DEV-only latency, product and country reported separately;
7. TEST lock with immutable run IDs;
8. fix the scan-file overwrite and the freeze guard.

Corrected execution order: Phases A, B and C with tests first, then the production rebuild and validation (Phase D), then the freeze checklist. No TEST evaluation at any point.

**Earlier list of next actions** (superseded by `IMPLEMENTATION_PLAN.md` §8; each needs explicit user authorisation):
1. ~~Decide the treatment of #81 `satellite antenna`~~: **decided 24 Nov 2026: exclude as Uncertain** (approved, not applied).
2. Authorise applying the review decisions:
   - remove the 3 Uncertain look-alikes (and #81 if decided) via the pre-declared mechanism;
   - for #81: list it under `EXCEPTIONS:` and set `REVIEWED: yes <name> <date>` in `p7_plain_scan_v4.txt`;
   - then `--stage build` and `--stage validate`;
   - record the exclusion counts.
3. Authorise implementing Option A (the pilot TEST exclusion list in `evaluate.py`, its hash in the manifest, plus a unit test) and the cluster sensitivity analysis.
4. Re-run the unit tests and the clean-environment reproducibility check. **Correction (24 Nov 2026):** `test_build_is_deterministic` failed because the builder applied recorded look-alike decisions implicitly. **Fixed in Phase A** (cause and fix: `IMPLEMENTATION_CHANGES.md` §7). After Phase A: experiment tests 71/71 pass, backend tests 63/63 pass.
5. Freeze: `run_all.py --stage freeze --approved-by "<author>"`, after authorisation.
6. Only then: `--stage tune` (DEV), then `--stage evaluate` (TEST, once).
7. Literature review and citation verification; conference verification; manuscript (≤ 6 pages, IEEE template); three-reviewer QA.

## 14. Repository state and important paths
- **Branch:** `research/option-a-evaluation` (pushed; level with `origin`).
- **Head before this checkpoint:** `91b7305`. The working tree was clean before this file was added. Checkpoint commit: `063c8db`. Last benchmark-changing commit: `a0129b8`.
- **`IMPLEMENTATION_PLAN.md`** (repository root): the approved-in-principle plan for applying the decisions and safeguards.
- **`main`:** was `01dde8b` until 27 Nov 2026, when PR #1 merged `research/option-a-evaluation` at `0e5a831` into `main` (merge commit `0383ff7`, tree identical to `0e5a831`; not part of the research branch). Later research-branch commits (approval record, manifest) are not on `main`. `main` must not be merged back into the research branch before the TEST evaluation.

| Path | Content |
|---|---|
| `backend/server.py` | Original B and S0 (unchanged) |
| `backend/lexitax_v2/` | S1 |
| `backend/tests/` | S1 tests and original-file integrity tests |
| `backend/requirements-research.txt` | `pycountry` (for S1) |
| `research_paper/` | All research documents (see §3 for precedence); `IMPLEMENTATION_CHANGES.md` (change log); `author_review_checklist.md` |
| `research_paper/experiments/run_all.py` | Stages: build, validate, pilot, smoke, freeze, tune, evaluate |
| `research_paper/experiments/config.json` | Seed, split, tuning grid and rule, statistics, sources |
| `research_paper/experiments/lexeval/` | Builders, `systems.py` (adapters and ladder), `scoring.py`, `stats.py`, `evaluate.py`, `tuning.py`, `latency.py`, `figures.py`, `pilot.py`, `eval_exclusions.py` (Phase B), `run_control.py` (Phase C) |
| `research_paper/experiments/data/external/` | HS mirror CSV, PROVENANCE (superseded), Unicode licence. The Unicode emoji file is a git-ignored, hash-checked cache |
| `research_paper/experiments/data/generated/` | Frozen benchmarks plus `VALIDATION_REPORT.md`, `build_log.json` and `MANIFEST.json` (frozen 27 Nov 2026) |
| `research_paper/experiments/pilot/` | Review sheets and records (§5–§7); `superseded/` holds blank v3 sheets |
| `research_paper/experiments/results/` | DEV outputs (`tuning_dev.json`, `latency_dev.json`, `dev/`, `dev_stage_record.json`, `dev_stage_logs/`) and the single TEST run (`runs/20261127T104925Z-0f293784/`, `test_runs.jsonl`, `test_stage_record.json`, `test_stage_logs/`), all 27 Nov 2026. `figures/` is empty |

## 15. Known documentation inconsistencies (stale text in older documents)
Newer documents take precedence; these older passages should be read as superseded:
- `experiments/dataset_sampling_rationale.md`: the body tables still describe the v3 P4 (EITHER) and Open Products Facts P7 (159 items). The v4 banner at the top supersedes them.
- `pre_evaluation_methodology_audit.md`: mentions Open Products Facts and EITHER (Phase 6). Superseded by `phase7_methodology_decisions.md`.
- `experimental_evaluation_plan.md`: the v2 body describes 40/60 splits and subsets PA–PE. Superseded by its v3/v4 banners.
- `annotation_guidelines.md` (v2) describes an earlier human workflow. Superseded by `experiments/pilot_review_sheet.md`, `experiments/p7_review_sheet.md` and Phase 7/8 documents.
- `experiments/p7_review_sheet.md`: the original body text says "Current draft P7: 116 items"; that is still correct, because no decisions have been applied.
