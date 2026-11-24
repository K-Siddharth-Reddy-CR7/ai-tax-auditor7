# Implementation change log (research branch `research/option-a-evaluation`)

Three layers are kept separate: **original implementation** (unchanged unless listed here), **research implementation** (new files), and **evaluation infrastructure** (new files under `research_paper/experiments/`).

## 1. Original implementation — files left byte-identical
`backend/server.py`, `backend/requirements.txt`, all eight dataset files (CSV/JSON), and `Majorpro (1).ipynb`. This is enforced by `backend/tests/test_original_untouched.py`, which checks SHA-256 against `main@01dde8b`. B and S0 are evaluated by calling the original functions directly.

## 2. Research implementation (C1 — approved)
| Change | Files | Why | Effect on original |
|---|---|---|---|
| S1 pipeline package | `backend/lexitax_v2/*` (new) | Corrected staged pipeline under study: validation, ISO 3166-1 jurisdiction identification separate from tax-data availability, evidence-based product abstention, no default rates or FX substitution | None. It reuses the original tables, `calculation_agent` and `PolicyRetriever` through a read-only loader |
| Tests | `backend/tests/*` (new) | 63 tests: unit, integration, determinism, byte-identity of original files, S0-equivalence on canonical inputs | None |
| Research dependency | `backend/requirements-research.txt` (new) | `pycountry==26.2.16` for S1 only | The original `requirements.txt` is unchanged |

The S1 product-matching parameters in `S1Config` are **provisional defaults**. The reported values will be selected on the DEV split by the pre-declared rule (`research_paper/experiments/config.json`).

## 3. Frontend claim corrections (C3 — approved)
These are text and label changes only; no logic was changed. The build was verified with `vite build`.
| File | Before | After | Why |
|---|---|---|---|
| `SystemBenchmark.jsx` | KPI cards "37.5 %", "100 %", "0 % False Negatives"; "Notebook Cell 58 Benchmark"; "EVALUATION BENCHMARK" | Two descriptive cards stating that the page is a checklist from source code, not a measurement, and that no measured values are shown; title "Implemented Processing Steps (from source code)"; label "DESCRIPTIVE - NOT A MEASUREMENT" | The figures were hard-coded literals, not measurements |
| `SystemBenchmark.jsx` | 8 capability rows incl. "Policy Lookup: baseline supported", "cognitive agents", "Dense vector … RAG", "cryptographic audit identifier" | 6 rows matching the code. The baseline performs **no** policy lookup; the policy step is lexical TF-IDF over placeholder records; the keyword flag always returns "cleared" with current data; the audit ID is time-based | Factual errors relative to `backend/server.py` |
| `AuditConsole.jsx` | Badges "AUDIT VERIFIED", "Verified Active" shown for every result | "PIPELINE COMPLETED", "Prototype policy record" | Nothing is verified; the badges were unconditional |
| `ThreeCanvas.jsx` | "dense TF-IDF vector retrieval … flagging BIS, CE, FDA permits"; "cryptographic audit ID … compliance verdict" | Lexical TF-IDF over prototype records plus keyword flag; trace plus timestamp-based ID | Not implemented as described |
| `HomePage.jsx` | "per WTO customs valuation rules", "dense vector retrieval … FTA exemptions automatically", "global harmonized tariff schedule catalog", "Export compliance certificates", "Cryptographic SHA-based audit identifier", "Levenshtein distance", "final compliance verdict", "full compliance at every step" | Statements matching the implementation (simplified valuation, lexical retrieval over prototype records, synthetic catalogue, browse view, time-based ID, exact/prefix/substring/word-overlap matching, trace) | Not implemented as described |

Product names, agent names, layout, styling and behaviour are unchanged. The README is unchanged; the authors may revise it.

## 4. Not done (deferred or declined)
- **C2 `/api/v2/audit` endpoint:** deferred by the authors until S1 is validated.
- No changes to the batch-auditor thresholds. They never fire on the shipped data; this is reported as a finding, not fixed.

## 5. Phase 6 changes (15 Nov 2026): evaluation infrastructure only
B, S0, S1 and the frontend are unchanged in this phase. Full rationale: `pre_evaluation_methodology_audit.md` §2.
| File | Change | Reason |
|---|---|---|
| `experiments/lexeval/build_products.py` | Rewritten: categories P1–P8 (855 items, was 6,096) | Formal HS texts dominated v2 (77 %); new categories target the research question |
| `experiments/lexeval/build_countries.py` | Subsets J1–J7; new fields `form`, `s1_builtin`, `cluster` | Separate codes and names; prevent overstating S1 on its own reference forms |
| `experiments/lexeval/refdata.py` | Open Products Facts loader (pinned commit, hash-checked download) | Informal out-of-catalogue product names |
| `experiments/lexeval/scoring.py` | EITHER outcome | Short forms: answer or abstain acceptable |
| `experiments/lexeval/stats.py`, `evaluate.py` | Cluster bootstrap CIs; cluster permutation test (primary); pooled filters; Wilson/McNemar renamed as item-level | Items are clustered; pooled claims exclude P8 and S1-built-in forms |
| `experiments/lexeval/latency.py`, `run_all.py` | Time the systems' own entry points | Adapter overhead biased latency |
| `experiments/lexeval/tuning.py`, `config.json` | Tuning on P2–P7; 30/70 split; design sizes; OPF pin; statistics settings | See audit |
| `experiments/lexeval/pilot.py` | v3 strata, one reviewer, look-alike confirmation sheet, overwrite protection | Minimal human workload |
| `experiments/tests/*` | New tests for EITHER, clustering and the permutation test | — |
| `experiments/data/generated/*` | Regenerated DRAFT (not frozen) | — |

## 6. Phase 7 changes (15 Nov 2026): evaluation infrastructure and review materials only
B, S0, S1 and the frontend are unchanged. Nothing is frozen, tuned or evaluated.
| File | Change | Reason |
|---|---|---|
| `experiments/lexeval/refdata.py`, `config.json`, `.gitignore` | Open Products Facts loader removed; pinned Unicode `emoji-test.txt` loader added; licence notice stored | OPF licence not established (author decision) |
| `experiments/lexeval/build_products.py` | P4 → single gold DECLINE, initialisms removed; P7 → Unicode names, whole-word look-alikes, non-goods filter, review-driven removals; P7 grouping by head word | Single gold labels; licensed data; leakage-safe split |
| `experiments/lexeval/build_countries.py`, `scoring.py`, `evaluate.py`, `validate.py`, `pilot.py`, tests | `expected_iso` → `gold_iso`, `expected_behaviour` → `gold_tax_action`; `system_iso` and safety flags in result rows; EITHER removed; `is_safe` | Separate gold identity from system behaviour (P08) |
| `experiments/lexeval/pilot.py`, `run_all.py` | Pinned v4 pilot (P06 redrawn); v4 look-alike sheet; plain-name scan; freeze refuses until the P7 review is complete; no overwrite of reviewed files | Human review workflow |
| `experiments/pilot/superseded/` | Blank (never reviewed) v3 sheets moved here, not deleted | Preserve history |

## 7. Phase A changes (24 Nov 2026): authoritative P7 review treatments (IMPLEMENTATION_PLAN.md Phase A)
B, S0, S1, the frontend, the committed generated benchmark files and all original review records are unchanged. Nothing was rebuilt in production, frozen, tuned or evaluated. Phases B–D are not implemented.
| File | Change | Reason |
|---|---|---|
| `experiments/pilot/authorised_review_treatments_v1.csv` | **New.** One row per P7 item (116): source review, item number, recorded decision, authorised treatment, reason, authoriser, date and authorisation record. 112 keep (13 Outside + 99 Clear); 4 exclude (couch and lamp, toothbrush, video game: Uncertain; satellite antenna: Flag for review, excluded as Uncertain by author decision) | Single authoritative decisions file (author decision 1) |
| `experiments/lexeval/pilot.py` | Added `review_records`, `validate_treatments`, `load_treatments`, `apply_review_treatments`, `provenance_log_entries`. Removed `lookalike_decisions` and `plain_exceptions` (the implicit path and the scan-file `REVIEWED` reader). Sheet writers create files with mode `x` and never overwrite an existing file | Validation against the review records; fix the scan-file overwrite |
| `experiments/lexeval/build_products.py` | Validates the decisions file before generation; P7 items are generated unfiltered; authorised exclusions are removed after `finalize`, logged as `review_exclusion`, and returned in full as audit rows (`EXCLUDED_FIELDS`). The build log records the SHA-256 of the decisions file and both review records | Builds depend only on explicit, hashed inputs; every other row is generated exactly as before |
| `experiments/run_all.py` | `--stage build` also writes `data/generated/excluded_items.csv`. New `freeze_preconditions()`: decisions file valid; benchmark P7 = keep set; audit file = exclude set with matching reasons; build log matches the current decisions file and review records. The scan file's `REVIEWED` line is no longer read. The manifest will also hash `excluded_items.csv` and the decisions file | Fix the freeze guard |
| `experiments/tests/test_review_treatments.py`, `tests/_helpers.py` | **New**, 55 tests. Temporary directories and copies of the review records only | Phase A acceptance tests |
| `experiments/tests/test_systems_and_data.py` | `test_build_is_deterministic` now builds with the authoritative decisions file. It requires byte-identity with the committed draft after adding back exactly the 4 authorised rows (pre-Phase-D), or full byte-identity (post-Phase-D); partial application fails. It also checks that the build leaves `pilot/` unchanged | Root-cause fix of the determinism failure (see below) |

**Determinism failure: cause and fix.** The committed draft was built at `a0129b8`, before any review decision existed. Afterwards, the builder treated the mere presence of decisions in `p7_lookalike_review_v4.csv` as an instruction to drop non-Outside look-alikes (`reviewed = any(decisions.values())`). The build output therefore depended on the mutable state of a review sheet, not on any explicit build input, and a fresh build dropped couch and lamp, toothbrush and video game (verified 24 Nov 2026: exactly these 3 IDs missing, no other difference). Now the only review input is the validated, hashed decisions file. A temporary-directory build equals the committed draft minus exactly the 4 authorised rows, with every other byte identical, and two builds are byte-identical. The committed draft is unchanged until the Phase D production rebuild.
