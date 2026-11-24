# RESEARCH_STATE.md — LEXITAX AUDIT research checkpoint

**Checkpoint date:** 24 Nov 2026.
**Written on branch:** `research/option-a-evaluation`, on top of commit `91b7305`. This file is committed as the next commit; run `git log -1` for its hash.
**Updated 24 Nov 2026: CURRENT STAGE = PLANNING COMPLETE; IMPLEMENTATION PENDING AUTHOR APPROVAL.** See `IMPLEMENTATION_PLAN.md`.
- The four P7 exclusions (§8) are **approved but NOT applied**.
- The eight-item pilot TEST exclusion is approved in principle but **NOT implemented**.
- The last commit that changed generated benchmark data, generation code or configuration is **`a0129b8`** (verified in git history).

**Purpose:** a self-contained handoff so a fresh session can continue the research without this conversation. Every number below was verified against repository files at the time of writing, unless it is marked **[UNVERIFIED]**.

---

## ⚠️ 0. NON-NEGOTIABLE RESEARCH INTEGRITY RULES (read first)
1. **Never tune on the TEST split.** S1 parameter selection uses DEV only (`lexeval/tuning.py` filters `split == "dev"`).
2. **Never use TEST results for any development, design or model-selection decision.** TEST is used once, after the freeze, for the final evaluation.
3. **The 8 pilot-reviewed TEST items must be excluded from final TEST metrics** (§5). As of this checkpoint the exclusion is **proposed but NOT implemented in code**. It must be implemented before any TEST evaluation.
4. **Every exclusion must be documented with its reason and count**, and reported in the paper.
5. **Uncertain items must never be silently treated as accepted examples.** The 3 look-alikes marked Uncertain and the 1 plain name marked "Flag for review" (§6–§8) may not be kept as gold DECLINE items without explicit author authorisation.
6. **Never invent results, metrics, statistical significance or experimental outcomes.** No experiment has been run (§13).
7. **Never claim capabilities that are not implemented.** No LLM, no generative RAG, no multi-agent autonomy, no valuation-discrepancy detector, no risk scorer, no consensus auditor, no fraud detection, no legal classification.
8. **Preserve the original baseline and application.** `backend/server.py` and the original datasets must stay byte-identical to `main` (enforced by `backend/tests/test_original_untouched.py`).
9. **Do not modify `main`.** Do not merge. Do not force-push.
10. **Do not apply manual review decisions, change benchmark labels, remove examples, or rebuild the benchmark without explicit user authorisation.** Note: `run_all.py --stage build` *would* apply the recorded look-alike decisions (§8), and `--stage pilot` would overwrite `pilot/p7_plain_scan_v4.txt`. Neither may be run until Phase A of `IMPLEMENTATION_PLAN.md` is implemented and authorised.
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

## 4. Benchmark: composition and splits (DRAFT, not frozen)
Files are in `research_paper/experiments/data/generated/`. They are deterministic (seed 20261114), reproduced byte-identically in a clean venv and across `PYTHONHASHSEED` values in Phase 6/7.

| File | SHA-256 |
|---|---|
| `product_benchmark.csv` | `4b69c5bb24ed519831490118e4d86ca2dfb38575cde4db5479c4e3feda1b5351` |
| `country_benchmark.csv` | `1bf3f48940c27b4ba7fad332bc8e0bbc367df1381a251e6345a3a6609444c929` |
| `malformed_inputs.csv` | `bb3af78811f382e8f1bcab7d622cfbe0737177a7a4644e8724b0258ef19655df` |

- `VALIDATION_REPORT.md`: 0 errors, 0 warnings.
- Split: group-level hash, **DEV 30 % / TEST 70 %**. Groups never straddle splits. DEV is used only for tuning. There is **no separate training split**: nothing is trained.

**Products: 809 items (DEV 272 / TEST 537)**
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
- **Not implemented:** `lexeval/evaluate.py` does not read `pilot_reviewed_items.json` yet.

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
| 8 pilot items in TEST | Inspected | Exclude from every final TEST metric via `evaluation_exclusions_v1.json`; rows preserved (`IMPLEMENTATION_PLAN.md` Phase B) | Approved in principle; **implementation not authorised** | **No** |
| 13 Outside look-alikes | Outside | Keep as gold DECLINE | **No** | No (they are already in the draft as DECLINE) |
| 3 Uncertain look-alikes (couch and lamp, toothbrush, video game) | Uncertain | Exclude; full rows kept in an audit file | **Yes: approved by the user on 24 Nov 2026** | **No.** To be applied via `pilot/authorised_review_treatments_v1.csv` (`IMPLEMENTATION_PLAN.md` Phase A). Note: the current builder would already drop them on any `--stage build` |
| #81 satellite antenna | Flag for review | **Author decision (24 Nov 2026): exclude as Uncertain.** The current code has no mapping for "Flag for review"; Phase A adds one via the decisions file, without editing the scan file | **Yes: approved** | **No** |
| 99 Clear plain names | Clear | Keep as gold DECLINE | No | No change needed |
| Freeze | — | `run_all.py --stage freeze` refuses unless all look-alikes are decided **and** the scan file says `REVIEWED: yes` | **No** | No |

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
- `tune` and `evaluate` are blocked until `data/generated/MANIFEST.json` exists with `--approved-by`.
- **Caution:** `lexeval/latency.py::measure` defaults to `split="test"`, timing systems on TEST inputs without scoring them. It is only invoked from `--stage evaluate`, which is freeze-gated. Do not call it before the freeze.
- Fuzzy-matching baseline: **deferred** until initial results (author decision).

## 10. Statistical requirements (`config.json` → `statistics`; `lexeval/stats.py`, `evaluate.py`)
- **Primary CIs:** cluster bootstrap (resample clusters; 95 % percentile). Item-level Wilson intervals are secondary.
- **Primary paired tests:** cluster-level two-sided sign-flip permutation test (10,000 permutations; exact if ≤ 16 non-zero clusters) with a cluster-bootstrap CI for the difference. **Holm** correction across the primary family of 18 tests: (B–S0, S0–S1, B–S1) × (decision-correct, silent-error) × (product, identification, tax behaviour).
- **Secondary:** exact McNemar (item-level). Ladder comparisons form a separate, exploratory family.
- **Small categories** (P4, P5, P6, J6, J7) are reported descriptively; no per-category significance claims.
- **Latency:** time the systems' own entry points (`latency.raw_systems`), not the evaluation adapters. 200 warm-up calls, 30 repetitions over 1,000 workload items, `perf_counter_ns`. Report mean, SD, median (bootstrap CI over repetition medians), p95, p99 and throughput, with the environment recorded. Results are indicative for a shared VM.
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
- freeze, tuning and evaluation;
- figures and results;
- manuscript (no draft exists);
- final submission checklist;
- one comprehensive PR to `main` (to be opened only after stable results; left unmerged).

**Current stage:** planning complete (`IMPLEMENTATION_PLAN.md`); implementation pending explicit author authorisation.

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
4. Re-run the unit tests and the clean-environment reproducibility check. **Correction (24 Nov 2026):** `tests/test_systems_and_data.py::test_build_is_deterministic` currently FAILS, because the builder already applies the recorded look-alike decisions. The "79 passing" figure is no longer valid. This is fixed by `IMPLEMENTATION_PLAN.md` Phases A and D.
5. Freeze: `run_all.py --stage freeze --approved-by "<author>"`, after authorisation.
6. Only then: `--stage tune` (DEV), then `--stage evaluate` (TEST, once).
7. Literature review and citation verification; conference verification; manuscript (≤ 6 pages, IEEE template); three-reviewer QA.

## 14. Repository state and important paths
- **Branch:** `research/option-a-evaluation` (pushed; level with `origin`).
- **Head before this checkpoint:** `91b7305`. The working tree was clean before this file was added. Checkpoint commit: `063c8db`. Last benchmark-changing commit: `a0129b8`.
- **`IMPLEMENTATION_PLAN.md`** (repository root): the approved-in-principle plan for applying the decisions and safeguards.
- **`main` @ `01dde8b`:** untouched. Original application and datasets (and README) are identical to `main`.

| Path | Content |
|---|---|
| `backend/server.py` | Original B and S0 (unchanged) |
| `backend/lexitax_v2/` | S1 |
| `backend/tests/` | S1 tests and original-file integrity tests |
| `backend/requirements-research.txt` | `pycountry` (for S1) |
| `research_paper/` | All research documents (see §3 for precedence); `IMPLEMENTATION_CHANGES.md` (change log); `author_review_checklist.md` |
| `research_paper/experiments/run_all.py` | Stages: build, validate, pilot, smoke, freeze, tune, evaluate |
| `research_paper/experiments/config.json` | Seed, split, tuning grid and rule, statistics, sources |
| `research_paper/experiments/lexeval/` | Builders, `systems.py` (adapters and ladder), `scoring.py`, `stats.py`, `evaluate.py`, `tuning.py`, `latency.py`, `figures.py`, `pilot.py` |
| `research_paper/experiments/data/external/` | HS mirror CSV, PROVENANCE (superseded), Unicode licence. The Unicode emoji file is a git-ignored, hash-checked cache |
| `research_paper/experiments/data/generated/` | Draft benchmarks plus `VALIDATION_REPORT.md`, `build_log.json` (no `MANIFEST.json` yet = not frozen) |
| `research_paper/experiments/pilot/` | Review sheets and records (§5–§7); `superseded/` holds blank v3 sheets |
| `research_paper/experiments/results/`, `figures/` | Empty (no results exist) |

## 15. Known documentation inconsistencies (stale text in older documents)
Newer documents take precedence; these older passages should be read as superseded:
- `experiments/dataset_sampling_rationale.md`: the body tables still describe the v3 P4 (EITHER) and Open Products Facts P7 (159 items). The v4 banner at the top supersedes them.
- `pre_evaluation_methodology_audit.md`: mentions Open Products Facts and EITHER (Phase 6). Superseded by `phase7_methodology_decisions.md`.
- `experimental_evaluation_plan.md`: the v2 body describes 40/60 splits and subsets PA–PE. Superseded by its v3/v4 banners.
- `annotation_guidelines.md` (v2) describes an earlier human workflow. Superseded by `experiments/pilot_review_sheet.md`, `experiments/p7_review_sheet.md` and Phase 7/8 documents.
- `experiments/p7_review_sheet.md`: the original body text says "Current draft P7: 116 items"; that is still correct, because no decisions have been applied.
