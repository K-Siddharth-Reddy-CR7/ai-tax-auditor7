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
