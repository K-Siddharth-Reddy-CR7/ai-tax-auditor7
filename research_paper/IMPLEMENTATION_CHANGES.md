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

## 8. Phase B changes (26 Nov 2026): TEST evaluation exclusions (IMPLEMENTATION_PLAN.md Phase B)
No evaluation, tuning, latency run, freeze or production rebuild was performed. Benchmark files, review records and the original application are unchanged.
| File | Change | Reason |
|---|---|---|
| `experiments/evaluation_exclusions_v1.json` | **New.** For each of the 8 pilot-inspected TEST items: pilot ID, item ID, benchmark, split, category, text, cluster, pilot decision, reason, source record. Also records the SHA-256 of the two pilot records, lists the two DEV pilot items as not excluded, and fixes the sibling clusters for the sensitivity analysis | Dedicated exclusion file (author decision 3) |
| `experiments/lexeval/eval_exclusions.py` | **New.** `validate_exclusions` rejects missing, duplicate and unknown IDs; DEV items; contradictions with the pilot record, the pilot sheet or the benchmark; IDs absent from or repeated in the benchmark; wrong sibling clusters; and changed source records. `load_test_items` (**the only TEST loader**) requires the manifest hash, removes the excluded IDs and returns the audit rows. `assert_no_excluded` is an independent row guard. `without_sibling_clusters` produces the sensitivity set | Single choke point |
| `experiments/lexeval/evaluate.py` | `load("test")` goes through `load_test_items`; any split other than dev or test is refused. `summarise_by` and `paired_tests` (cluster bootstrap, permutation test, McNemar) call the guard. `evaluate()` guards item rows, writes `<tag>_test_excluded_from_metrics.csv`, and writes the separate sensitivity outputs (`<tag>_sensitivity_siblings_removed_test_*`, `..._sensitivity_siblings_info.json`) | Every TEST metric path uses the mechanism |
| `experiments/run_all.py` | Freeze guard also validates the exclusions; the manifest records `evaluation_exclusions_sha256`; `--stage evaluate` refuses a manifest without it and passes it to every TEST evaluation | Hash fixed at freeze; evaluation stops on mismatch |
| `experiments/lexeval/validate.py` | Validation report includes the exclusion check and the file's SHA-256 | Plan, Phase B |
| `experiments/tests/test_eval_exclusions.py` | **New**, 43 tests. End-to-end checks use synthetic benchmarks in temporary directories only | Phase B acceptance tests |
| `experiments/tests/test_review_treatments.py` | The `built` fixture also copies the (unchanged) country benchmark into its temporary directory, which the freeze guard now needs | No assertion changed |

**Not covered here (later phases):**
- `lexeval/latency.py::measure` still defaults to TEST inputs (timing only, no metrics). It is reachable only through the freeze-gated evaluate stage, and Phase C makes latency DEV-only.
- `figures.risk_coverage` expects a TEST sensitivity grid file that no code produces yet. Any future producer must obtain rows through `load_test_items`.

## 9. Phase C changes (26 Nov 2026): TEST route, DEV-only tuning and latency, figures, run controls (IMPLEMENTATION_PLAN.md Phase C)
No tuning, latency measurement, freeze, manifest or TEST evaluation was performed. Benchmark files and review records are unchanged.
| File | Change | Reason |
|---|---|---|
| `experiments/lexeval/run_control.py` | **New.** `verify_manifest`: every frozen hash (benchmarks, `excluded_items.csv`, config, decisions file, exclusions file, `approved_by`). `open_run`: requires the manifest, the DEV tuning record and `--authorised-by`, plus `--rerun-reason` after any earlier run; creates `results/runs/<UTC-timestamp>-<hash8>/` (never reused); writes `run.json` with all input and code hashes; appends to a hash-chained `results/test_runs.jsonl`. `close_run`: hashes all outputs, makes them read-only, logs completed or aborted. `require_run` rejects missing, forged or closed handles | Permanent TEST run controls; single TEST route |
| `experiments/lexeval/evaluate.py` | `evaluate()` and `load()` no longer accept an exclusion hash: TEST requires an open run, and the hash comes from its verified manifest. `run_product_task` and `run_country_task` call `check_items`: excluded IDs are always refused, split must be dev or test, and TEST rows need an open run. Item rows carry `split`. TEST outputs go to the run directory with exclusive create. A provenance file is written per evaluation, and `ladder_pairs()` is added. DEV outputs default to `results/dev` | Phase B audit routes 2 and 3 |
| `experiments/lexeval/eval_exclusions.py` | `write_audit(..., exclusive)` | Never overwrite TEST outputs |
| `experiments/lexeval/tuning.py` | `assert_dev_only` on every input path (file or caller-supplied rows; missing, empty, `test`, mixed and wrong-case splits rejected); `select()` factored out with the rule unchanged; the record states split `dev`, the input hash and the DEV item-ID hash, and is created exclusively. DEV P1–P7 grid metrics are stored for the figure only (not used in selection); `load_tuned` refuses non-DEV records | DEV-only tuning |
| `experiments/lexeval/latency.py` | DEV-only `workloads()` and `measure()`: TEST is refused and there is no fallback. Product and country workloads are timed separately, with per-call median, p95, p99, mean and SD, throughput and run-to-run variability. An interpretation note is recorded; `results/latency_dev.json` is created exclusively | DEV-only latency |
| `experiments/lexeval/figures.py` | `risk_coverage` (TEST grid, no producer) replaced by `risk_coverage_dev` (DEV inputs only). `dev_figures()` and `figures_for_test_run()` check split and excluded IDs in item outputs before plotting, and record input hashes. `outcome_bars` handles one subset | Phase B audit route 4; author decision on the DEV-only figure |
| `experiments/run_all.py` | `_require_frozen` verifies every manifest hash. `tune` adds the DEV evaluation and DEV figure; new `latency` stage; `evaluate` needs `--split test --authorised-by` (and `--rerun-reason` for reruns) and runs primary, ladder and TEST figures inside one logged run | Single TEST route |
| `experiments/config.json` | `latency` block: `workload_items: 1000` replaced by `split: dev` and separate product and country workload definitions | Approved latency design |
| `experiments/tests/test_phase_c.py`, `tests/_runfix.py` | **New**, 59 tests on synthetic benchmarks and manifests in temporary directories | Phase C acceptance tests |
| `experiments/tests/test_eval_exclusions.py` | The TEST fixture now opens an authorised run instead of passing a hash; two tests were rewritten for the new API (refusal without an authorised run; manifest lacking the exclusion hash). Leak checks extended to the run records | Required by the API change; assertions kept |
| `experiments/tests/test_pipeline_dryrun.py` | `test_latency_code_path` uses the new DEV-only result structure (both workloads checked) | Required by the API change |

**Limits:**
- Python cannot prevent deliberately written code from re-implementing the evaluation. The controls make the sanctioned route the only one this code accepts, and make any extra TEST run visible in the log.
- The tests run as root, so read-only file modes are checked by their mode bits.

## 10. Phase C.1 changes (26 Nov 2026): corrections from the Phase C audit
No tuning, latency measurement, freeze, manifest or TEST evaluation was performed. Benchmark files, review records and the selection rule are unchanged.
| File | Change | Reason |
|---|---|---|
| `experiments/lexeval/run_control.py` | **`reconcile()`** before every TEST run. It detects: a missing log while evidence exists; a broken chain (edited, removed, duplicated or reordered lines); a truncated last line; whole tail entries removed (orphaned run directory, or close.json without an end entry); a log entry without a directory; missing, corrupt or modified run.json/close.json/outputs; files added after closing; duplicate or out-of-order events; wrong previous-run references; malformed run IDs; unmatched recovery records. **`recover()`**: authorised, evidence-preserving acknowledgement (recovery record plus appended entry; a missing log is never regenerated). **Code identity** (`CODE_IDENTITY_PATTERNS`, `code_identity`, `verify_code`, `manifest_record`): clean tree required at freeze; at TEST, identity equal, tree clean, and HEAD equal to the frozen commit or a descendant that changes no identity path. `close_run` re-verifies the manifest (on failure: closed as aborted, then raises) and writes `close.json`. `run.json` adds `environment` (Python and all installed package versions) and `frozen_git_commit` | R1, R2, R3 |
| `experiments/lexeval/tuning.py` | `load_tuned(expected_sha256=...)` hashes the exact bytes it parses. `full_pipeline_grid()` (figure and sensitivity only) records resolver-level and full-pipeline scores, their differences, the selected setting and its full-pipeline point; differences are preserved. Tie-break order documented (`FEASIBLE_ORDER`, `INFEASIBLE_ORDER`) and recorded in the tuning record; selection logic unchanged | R3; risk–coverage correction; tie-break clarification |
| `experiments/lexeval/figures.py` | `risk_coverage_dev` draws the full-pipeline grid, rings the selected setting, shows the B/S0/S1 DEV points, and carries the title "S1 full-pipeline risk–coverage across the tuning grid (DEV)" with a note that selection was resolver-level. `dev_figures` records the S1 operating point against its grid point and refuses a grid from another tuning record | Risk–coverage correction |
| `experiments/run_all.py` | `freeze` uses `manifest_record` (clean tree, code identity, commit; never overwrites a manifest). `tune` adds the full-pipeline grid. `evaluate` loads the tuning record with the hash recorded at open. New `recover-runs` stage (`--recovery-reason`) | R1–R3 |
| `experiments/tests/test_phase_c1.py` | **New**, 59 tests (reconciliation and tampering, recovery, code identity with temporary git repositories, provenance re-checks, full-pipeline grid, tie-breaks) | Phase C.1 acceptance tests |
| `experiments/tests/_runfix.py` | Synthetic manifests now come from `manifest_record` with a temporary git repository holding copies of the code-identity files | Tests independent of the real working tree |
| `experiments/tests/test_phase_c.py` | State-aware: the setup check compares the real results/ tree and MANIFEST.json before and after each test. `test_real_repository_has_no_runs_or_manifest` became `test_real_repository_run_state_is_consistent` (strict "no outputs" before the freeze; verify and reconcile after). The latency refusal test supplies the unfrozen state explicitly. Figure tests updated for the grid input; `close.json` expected in run outputs | Item 6; API changes |
| `experiments/tests/test_eval_exclusions.py` | Leak-check file list includes `close.json` | New run file |

**Correction:** the configured tuning grid has 49 settings, not the 61 stated in the Phase C audit report.

**Limits:**
- Local hash chains are not cryptographic proof against an actor who consistently rewrites all local evidence; a test documents this.
- Exact git-commit equality at TEST time is replaced by "frozen commit or a descendant with no changes to identity paths", because `MANIFEST.json` must be committed after the freeze.
