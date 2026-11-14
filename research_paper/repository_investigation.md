# LEXITAX AUDIT — Phase 1 Repository Investigation Report

**Scope.** Read-only investigation of `K-Siddharth-Reddy-CR7/ai-tax-auditor7`, commit `01dde8b` (branch `main`, 2 commits total). No source code, dataset, configuration or README file was modified.
**Date.** 14 November 2026.
**Method.** Full reading of `backend/server.py`, all frontend components, all four datasets (CSV and JSON), the notebook `Majorpro (1).ipynb` (60 cells, including stored outputs), the README, the reference paper and the IEEE template. Behavioural claims were checked by importing `backend/server.py` in an isolated virtual environment and calling its functions directly (no server start-up, no file writes). Every number in this report can be regenerated with the scripts in `investigation_scripts/` (see the README there).

> **Bottom line.** The repository implements a **deterministic, six-step sequential pipeline** that (1) validates inputs, (2) maps a product name to a catalogue entry by string matching, (3) retrieves a policy record with TF-IDF cosine similarity plus metadata bonuses, (4) looks up a single country-level duty and VAT rate, (5) computes a landed cost, and (6) assembles a trace. It does **not** implement the valuation-discrepancy detector, risk scorer or consensus/reconciliation auditor described in the README, it has **no generative component**, and the shipped data are **synthetic and partly templated** with **no ground-truth labels**. On all 400 sample transactions the "agentic" pipeline and the single-pass baseline produce **identical landed costs and identical HS codes**. The paper described in the brief cannot be written truthfully from the current repository. Section 9 sets out the choices that would make a defensible paper possible.

---

## Contents
1. Verified technical architecture
2. Stage-by-stage analysis (actual six stages vs. README six agents)
3. Baseline and comparison endpoints
4. Frontend and integration
5. API and deployment
6. Dataset quality and provenance report
7. Notebook analysis
8. Experimental evidence discovery
9. Unsupported or exaggerated claims
10. Missing experiments (prioritised)
11. Preliminary contribution and novelty assessment
12. Reference paper structural analysis
13. Template analysis
14. Timeline feasibility (November 2026)
15. Questions requiring author clarification

---

## 1. Verified technical architecture

```
HTTP JSON ──► Flask route (/api/audit/agentic)              backend/server.py:465-479
                 │
                 ▼  run_agentic_auditor_pipeline()           server.py:389-396
   ┌────────────────────────────────────────────────────────────────────────┐
   │ 1 input_agent        type-cast & presence check           :147-169     │
   │ 2 product_agent      catalogue string match → HS, category:171-216     │
   │ 3 rag_policy_agent   TF-IDF + bonus retrieval, keyword flag:218-259    │
   │ 4 tax_agent          country lookup → duty %, VAT %, ccy  :261-292     │
   │ 5 calculation_agent  CIF-style landed-cost arithmetic     :294-324     │
   │ 6 report_agent       step trace, latency sum, id, time    :326-387     │
   └────────────────────────────────────────────────────────────────────────┘
                 │  (one mutable Python dict passed and mutated in order)
                 ▼
            JSON response {success, data}
```

Verified properties:

| Property | Finding | Evidence |
|---|---|---|
| Agent independence | None. Each "agent" is a plain Python function that receives and mutates one shared `dict`. There is no message passing, no autonomy, no goal, no negotiation and no feedback loop. | `server.py:389-396` |
| Execution order | Fixed and hard-coded: Input → Product → RAG Policy → Tax → Calculation → Report. | `server.py:390-395` |
| Control flow | Linear. No stage can veto, revise or re-invoke another. An exception in `input_agent` aborts the request; no other stage raises. | `server.py:153-157, 475-479` |
| LLM / ML usage | None in the backend. No model is trained or loaded. Dependencies are `flask` and `flask-cors` only. | `backend/requirements.txt` |
| Generation | None. The "RAG" stage retrieves and copies stored strings; nothing is generated. | `server.py:229-236` |
| Determinism | Deterministic for identical inputs, except `audit_id`, `timestamp` and latency fields. | `server.py:385-386` |
| Synchronous? | Yes. Per-request, single-threaded within a request. Concurrency relies on Flask's development server (threaded by default). | `server.py:675-678` |
| Persistence | None. Datasets are loaded into memory at import time; no database; audit results are not stored. | `server.py:29-32` |
| External services | None at runtime. | — |

**Interpretation.** The defensible description is a *modular, sequential, rule-based decision-support pipeline*. Calling the stages "agents" is a naming convention, not a multi-agent system in the technical sense of the MAS literature (autonomous entities with their own goals, perception and interaction protocols). The manuscript should either say "stage"/"module", or define "agent" narrowly and explicitly ("a single-responsibility processing function").

---

## 2. Stage-by-stage analysis

### 2.0 README agents vs. implemented stages

| README agent (`README.md:40-46`) | Implemented? | What actually exists |
|---|---|---|
| A. Classification Agent: "evaluates descriptions, category match scores, validates HS-6" | **Partially** | `product_agent`: catalogue *lookup* by string match. No scoring, no confidence, no validation of a declared HS code (there is no declared HS input). |
| B. Tariff & Tax Engine: "exact statutory customs duty, VAT/GST, assessable freight values" | **Partially** | `tax_agent` + `calculation_agent`: one *country-level* duty rate and one VAT rate per destination; HS code does not affect duty. |
| C. RAG Policy Retriever: "semantic TF-IDF search over 240+ policies" | **Yes, as lexical retrieval** | `PolicyRetriever` (TF-IDF, cosine, metadata bonus). No generation; corpus is templated (§6.3). |
| D. Valuation & Discrepancy Detector: "deviation against historical commodity benchmarks" | **No** | No benchmark prices in any dataset; no deviation computation anywhere in the code. |
| E. Risk & Anomaly Scorer: "composite risk percentiles … trade routes, value anomalies" | **No** | Only a 3-level keyword flag inside the policy stage (§2.3). No score, no percentiles, origin country unused. |
| F. Consensus & Reconciliation Auditor: "COMPLIANT / FLAGGED / WARNING" | **No** | `report_agent` only formats a trace. None of the strings COMPLIANT, WARNING or FLAGGED appears in the agentic code path. `FLAGGED` exists only in `/api/transactions` (§3.3). |

The landing page (`frontend/src/pages/HomePage.jsx:535-540`) lists the six stages that are actually implemented (Input, Product, RAG Policy, Tax, Calculation, Report). The README lists a different, aspirational set.

### 2.1 Stage 1: Input stage (`input_agent`, `server.py:147-169`)
- Casts `price`→`float`, `quantity`→`int`, `shipping`→`float`. On failure it raises `ValueError`, which the route returns as HTTP 400.
- Presence check happens *before* `.strip()`, so a whitespace-only product name passes. It is then stripped to `""`, and `product_agent` matches it to the first catalogue item ("Laptop Standard"). Verified in `02_pipeline_behaviour.py`.
- No range checks. A negative price produces a negative landed cost (−129.80, verified). `quantity=0` is accepted. `quantity=2.7` (JSON number) is truncated to 2 silently, but `"2.7"` (string) is rejected.
- `source_country` is carried through but **never used** in any computation, retrieval or risk logic.

### 2.2 Stage 2: Product / "classification" stage (`product_agent`, `server.py:171-216`)
The mechanism is a three-tier string match over the 1,200 catalogue names, with first-match-wins in catalogue order:
1. `name == query or name.startswith(query)` (case-insensitive);
2. `query in name` (substring);
3. maximum token-set overlap |tokens(query) ∩ tokens(name)|; ties go to the earliest item.
4. **Fallback:** if nothing matches, a fabricated record `{HS_Code: "8471.30", Category: "Electronics"}` is returned (`:203-209`).

Observations:
- This is **lookup**, not classification or validation. It never checks a declared HS code, because the API does not accept one. No confidence or match score is output.
- The fallback silently assigns an HS code from Chapter 84 (computing machinery) to *any* unrecognised product. Verified: "Cotton T-Shirt" → 8471.30 / Electronics; "insulin" → 8471.30 / Electronics; "Smartphone" → 8471.30. The baseline returns `HS_Code: "N/A"` for the same inputs.
- The fallback code uses the dotted format "8471.30", while the catalogue uses six undotted digits ("847130"). The format is inconsistent.
- Substring matching causes semantic errors in both pipelines. Verified: "Car" → "Memory **Car**d Standard" (852351).
- Token overlap enables some useful recovery ("Gaming Laptop" → Laptop Standard, where the baseline gives N/A) but also wrong mappings ("notebook computer" → Desktop Computer Standard).
- HomePage claims "Levenshtein distance" (`HomePage.jsx:536`). **No edit-distance computation exists** anywhere in the repository.
- On exact catalogue names both pipelines self-match 1,200/1,200 (`04_catalog_and_tariff_checks.py`).

### 2.3 Stage 3: Policy retrieval (`PolicyRetriever` `server.py:66-143`; `rag_policy_agent` `:218-259`)
Implemented formulation (reconstructed exactly from code):

- Tokenisation: `re.findall(r'\w+', text.lower())`. No stop-word removal, stemming or n-grams.
- Document text: `Country ⊕ Category ⊕ Policy_Summary ⊕ Compliance_Note`.
- Term frequency: raw count *c(t,d)*.
- IDF (smoothed, scikit-learn style): **idf(t) = ln((N+1)/(df(t)+1)) + 1**, N = 240. This is *not* the textbook `log(N/(1+df))`; the paper must use the implemented form.
- Weights w(t,d) = c(t,d)·idf(t), then L2-normalised. Query terms absent from the vocabulary get idf = 1 (`:110`), but they contribute nothing to the dot product.
- Score: **s(q,d) = cos(q,d) + 0.4·𝟙[country(d)=dest] + 0.3·𝟙[category(d)=cat]**, the cosine being the dot product of unit vectors. The bonus is additive and is not a filter.
- Query built by the agent: `"{destination} {category} import policy and compliance requirements"`; top-k = 3; top-1 drives the output.
- Empty query → returns the first *k* policies unscored (`:103-104`).
- **No similarity threshold.** A top-1 result is always returned, however weak.

Compliance flag (`:238-248`): a substring test of the top-1 policy text against fixed keyword lists. "prohibited/banned/embargo/sanction" → `CRITICAL_PROHIBITED`. "license/certificate/bis/ce mark/fda/permit/inspection" → `REQUIRES_PERMIT`. Otherwise `STANDARD_CLEARANCE`. Note that `"bis"` is a raw substring test and would fire on any word containing "bis".

Effect on this dataset:
- **0 of 240 policy texts contain any trigger keyword**, so the risk flag is `STANDARD_CLEARANCE` for every possible input (verified: 400/400 sample transactions).
- All 240 policies share **one identical summary and one identical compliance note** (§6.3). The vocabulary is **69 terms**. Retrieval therefore differs only by country and category tokens, and the returned text is the same string for every query.
- Top-1 policy matches the destination country 400/400 times, and matches (country, category) 360/400 times. The 40 misses are exactly the transactions whose category ("Office Equipment") has no policy record. With bonuses switched off the top-1 result is identical in 400/400 cases. In effect the retriever acts as a metadata lookup.
- Retrieved text has **no effect** on duty, VAT or landed cost. Its only downstream effect is the keyword flag, which never fires.

The stage is **lexical information retrieval**. It is **not** retrieval-augmented *generation*: no language model consumes the retrieved text. The notebook's retriever is different (dense MiniLM embeddings with ChromaDB, §7).

### 2.4 Stage 4: Tax-rate lookup (`tax_agent`, `server.py:261-292`)
- Exact case-insensitive country match first, then a **bidirectional substring match** (`dest in country or country in dest`), then a fallback of 5 % duty, 10 % VAT, USD.
- Verified mis-resolutions: "US" → **Australia** (because "us" ⊂ "Australia"); "Niger" → Nigeria. Unknown names ("Atlantis", "USA", "UK") silently receive the 5 %/10 % USD default with **no warning**. "Korea" → South Korea is a correct partial match.
- Rates depend only on the destination country. **HS code, origin and preferential agreements have no influence** (`Default_Import_Duty_Percent` is a single number per country).

### 2.5 Stage 5: Calculation (`calculation_agent`, `server.py:294-324`)
With unit price *p*, quantity *q*, freight *f*, duty rate *r_d* and VAT rate *r_v* (both in %):

- Product cost P = p·q
- Customs (assessable) value V = P + f (CIF-like, but without insurance)
- Duty D = V·r_d/100
- Taxable value T = V + D
- VAT/GST G = T·r_v/100
- Landed cost L = T + G = V(1 + r_d/100)(1 + r_v/100)
- Effective tax rate = (D+G)/V·100; per-unit tax = (D+G)/q; per-unit landed = L/q
- Local currency = L × static rate (`EXCHANGE_RATES`, `:37-64`)

Assumptions and defects the paper must state:
- All inputs are assumed to be in USD. Exchange rates are static and undated, with no source.
- **5 of 40 destination currencies (DKK, ARS, CLP, EGP, NGN) are missing from the exchange-rate table**, so local amounts for Denmark, Argentina, Chile, Egypt and Nigeria are silently computed at a rate of 1.0.
- The VAT base "customs value + duty" is a common simplification. Insurance, other surcharges, excise, anti-dumping duty, de minimis thresholds and the FOB valuation basis used by some jurisdictions are not modelled.
- Divisions by `quantity or 1` mask quantity = 0.

### 2.6 Stage 6: Report (`report_agent`, `server.py:326-387`)
- Builds a six-element step list, sums stage latencies measured with `time.time()`, and generates `audit_id = "AUD-" + (ms_epoch mod 10⁶)`. The id repeats every 1,000 s, so it is **not unique and not cryptographic** (HomePage claims "cryptographic audit ID", `HomePage.jsx:540`).
- It produces no verdict. The UI's "AUDIT VERIFIED" badge (`AuditConsole.jsx:375-378`) and "Verified Active" badge (`:467`) are **hard-coded** and shown for every result.

---

## 3. Baseline and comparison endpoints

### 3.1 `/api/audit/normal` → `run_normal_auditor_pipeline` (`server.py:398-450`)
- Product: substring match only. If nothing matches → `HS_Code: "N/A"`, category "General" (it abstains instead of fabricating).
- Country: exact match only, falling back to 5 %/10 % USD.
- **Same arithmetic** as `calculation_agent`.
- No retrieval, no keyword flag, no trace, no input validation beyond the numeric cast.
- Its docstring says it replicates notebook Cell 55. It differs from Cell 55, which *stops* with "Country not found" instead of applying defaults.

### 3.2 Shared components and equivalence
Both pipelines read the same `PRODUCTS` and `TAXES` tables and apply the same formula. Consequences, verified on all 400 sample transactions:
- Landed-cost difference agentic − baseline = **0.00 in 400/400 cases**.
- HS code agrees with the transaction's own HS label in **400/400** (agentic) and **400/400** (baseline).

The two pipelines diverge only on **non-catalogue product strings** and **non-canonical country names**, and the agentic pipeline is not uniformly better there (e.g. US → Australia; T-shirt → computing machinery).

### 3.3 `/api/audit/compare` (`server.py:496-526`)
- The 8-row "features" matrix is a **hard-coded literal** (`:510-519`), not a measurement. It lists "Policy Lookup: normal = True", although the baseline performs no policy lookup.
- `cost_difference` is the only computed comparison field, and it is 0 for all catalogue/canonical inputs.
- `source_country` is not forwarded to either pipeline (`:506-507`).

### 3.4 `/api/transactions` (`server.py:528-609`) — the only place a FLAGGED status exists
- Recomputes landed cost per transaction (fallback rates 10 %/12 %, which differ from the 5 %/10 % elsewhere).
- Flags if duty > 5,000 USD, or else if duty rate ≥ 15 %.
- **Neither condition can trigger on the shipped data.** The maximum duty rate is 10 %, and the maximum computed duty is 1,308.60 USD. Verified: 0/400 FLAGGED. The batch view therefore always shows "0 / n flagged".

---

## 4. Frontend and integration

| Component | Operational? | Notes |
|---|---|---|
| `AuditConsole.jsx` | Yes; calls `/api/audit/agentic` | Displays cost breakdown, policy text and trace. `risk_level`/`risk_verdict` are **not displayed**. Success badges are hard-coded. |
| `BatchAuditor.jsx` | Yes; calls `/api/transactions` | Paginated table. "Audit" button opens a modal of pre-computed values; it does **not** run the pipeline. |
| `PolicyExplorer.jsx` | Yes; calls `/api/policies` | Category list (`:6-15`) includes Machinery, Chemicals, Food & Agriculture, Pharmaceuticals, Automotive. Only Automotive exists in the policy data, and none of these is a product category. |
| `SystemBenchmark.jsx` | **Static** | `BENCHMARK_DATA`, "37.5 %", "100 %" and "**0 % False Negatives**" are literals (`:5-54, 86-104`). No API call. |
| `ThreeCanvas.jsx`, `HomePage.jsx` | Visual only | Supporting interface; no bearing on audit correctness. |
| `api.js` | Thin `fetch` wrappers | `runCompareAudit` and `runNormalAudit` are defined but not called by any component. The compare button was removed (`AuditConsole.jsx:345`). |

---

## 5. API and deployment

- Routes: `/api/health`, `/api/stats`, `/api/countries`, `/api/products`, `/api/policies`, `/api/transactions`, `/api/audit/{agentic,normal,compare}`.
- Request schema (agentic/normal/compare): `product_name, destination, price, quantity, shipping[, source_country|origin]`. **The README's sample request (`declared_value, declared_duty, declared_vat`) is not read by the backend.** Sending it verbatim returns price 0, quantity 1, landed cost 0.00 (verified).
- `request.get_json(force=True)` with malformed JSON produces an unhandled 400 HTML response. Non-integer `limit`/`offset` cause HTTP 500.
- CORS open to all origins; no authentication; Flask development server (`app.run`); no WSGI or production configuration; no Docker; no CI.
- Latency is self-reported per stage with `time.time()`. There is no benchmark harness in the repository.
- Preliminary in-process timing (investigation only, not a paper result; 5×400 calls, 4-vCPU Intel Xeon @ 2.10 GHz, Python 3.13): agentic mean 0.33 ms, median 0.28 ms, p95 0.51 ms; baseline mean 0.027 ms. The agentic overhead is dominated by the linear scan over 240 policy vectors and 1,200 products.

---

## 6. Dataset quality and provenance report

All four CSV/JSON pairs are **cell-for-cell identical** (verified). No nulls, no duplicate rows.

### 6.1 `products` (1,200 × 5: Product_ID, Product, HS_Code, Category, Unit)
- Composition: **60 base product types × 20 synthetic variant suffixes** (Standard, Basic, Premium, Pro, Advanced, Lite, Plus, Max, Mini, Ultra, Gen 1–3, Series A–C, Model X–Z, 2026), e.g. "Laptop Model X", "Laptop 2026".
- 43 distinct HS-6 codes, all six digits. Each base type maps to exactly one code.
- 12 categories (Home Appliances 280, Electronics 260, Computer Accessories 140, Computer Components 120, Networking 80, Personal Care 80, Gaming 60, Electrical Equipment 60, Office Equipment 40, Lighting 40, Audio Equipment 20, Renewable Energy 20). Unit = "Piece" for all rows.
- **No benchmark or unit-price column.** The README's "benchmark unit prices" (`README.md:114`) do not exist.
- Coverage is limited to consumer electronics, appliances and related goods. The HS codes have not been checked against the HS nomenclature in this phase; that check is recommended.

### 6.2 `taxes` (40 × 4: Country, Currency, GST_VAT_Percent, Default_Import_Duty_Percent)
- VAT 0–25 % (mean 15.7). Duty: integers 5–10 % (mean 7.1).
- The VAT figures resemble published standard rates for several countries, but no source or date is recorded.
- **Internal validity problem:** the 13 EU member states carry *different* duty rates (Germany/France/Italy/NL/BE/PL/AT/GR 8 %; Spain/Ireland/Portugal/Sweden/Denmark 7 %). EU members apply a common external tariff, so a single "default" duty per member state cannot be correct. More generally, real duties are set per tariff line and per origin, not per country.
- "United States 0 % VAT" reflects the absence of a federal VAT. State sales taxes are not modelled.

### 6.3 `trade_policies` (240 × 6)
- 40 countries × 6 categories (Electronics, Computer Accessories, Home Appliances, Automotive, Medical Supplies, Textiles).
- **Policy_Summary has 1 unique value** ("Customs documentation and applicable import requirements apply.") across all 240 rows.
- **Compliance_Note has 1 unique value** ("Verify HS classification, origin, tariff treatment, exemptions and current requirements.").
- **Source_Type = "Prototype policy record for academic system testing."** for all 240 rows.
- Category mismatch: 9 of 12 product categories have no policy, and 3 policy categories (Automotive, Medical Supplies, Textiles) have no products.
- Consequence: these are **placeholder records, not trade policies**. Retrieval-quality metrics on this corpus would be meaningless.

### 6.4 `sample_transactions` (400 × 8: Transaction_ID, Product, HS_Code, Origin_Country, Destination_Country, Unit_Price_USD, Quantity, Shipping_USD)
- **Deterministically generated:**
  - Products are catalogue items 1–400 in order.
  - Unit price starts at 87.25 and rises by 37.25 per row, wrapping at about 1,502.75.
  - Quantity cycles 1…12.
  - Freight rises by 18.5, cycling 20–279.
  - Each of the 40 origins and 40 destinations appears exactly 10 times; destination = origin index + 8.
- Categories covered by the 400 rows: Electronics 240, Computer Accessories 120, Office Equipment 40.
- **No declared duty, declared VAT, declared value, audit status or any label.** The README's "empirical audit status" (`README.md:117`) does not exist.
- These are synthetic records, not customs declarations or commercial invoices.

### 6.5 Provenance
The notebook loads all four files from an uploaded `AI_Tax_Auditor_Large_Datasets.zip` (Cells 2–3). No generation script, source list or licence for the data is present. Given the arithmetic progressions, uniform cycling and templated text, the data should be described as **synthetically generated prototype data**. The authors must confirm how they were produced (Q3).

---

## 7. Notebook analysis (`Majorpro (1).ipynb`, 60 cells, Colab, Python 3.13)

| Cells | Content |
|---|---|
| 0–10 | Install; Colab upload; load CSVs; `head()`; counts (1200/40/240/400). |
| 11–24 | String-contains product search; landed-cost function (same formula as the backend); policy lookup by exact (country, category); demo calls (Laptop→India = 2,206.60 USD). |
| 25–33 | First "agent" version: input / product / policy / tax / calculation / report as functions; exact-match only. |
| 34–54 | **Dense retrieval:** `sentence-transformers` `all-MiniLM-L6-v2` + in-memory ChromaDB over the 240 policy texts; `rag_policy_agent` uses top-1; `run_agentic_auditor` prints "RAG Status: SUCCESS" unconditionally. |
| 55–57 | `normal_auditor` and a side-by-side print for one input (Laptop→India), giving identical landed cost 2,206.60. |
| 58 | Bar chart of **hand-entered 0/1 capability vectors** (`normal_system=[1,1,1,0,0,0,0,0]`, `agentic=[1]*8`), including "AI Explanation", which is not implemented anywhere. |

Findings:
- **No EDA, no distribution plots, no classification experiment, no anomaly detection, no statistics, no metrics.** The README's description (`README.md:246-249`) is not supported.
- The notebook retriever (dense, MiniLM) **differs** from the backend retriever (sparse TF-IDF). The backend is the deployed one.
- Outputs are reproducible in principle given the zip, but the notebook depends on Colab upload and on network access to download the model.

---

## 8. Experimental evidence discovery

A repository-wide search for evaluation outputs, metrics, logs, result files and benchmarks found:

| Evidence type | Present? | Location / note |
|---|---|---|
| Classification metrics (accuracy/P/R/F1, confusion matrix) | **No** | none |
| Anomaly-detection results | **No** | none |
| Retrieval metrics (P@k, MRR) | **No** | none |
| Latency/throughput measurements | **No** | per-request self-timing only |
| Baseline-vs-proposed quantitative comparison | **No** | `SystemBenchmark.jsx` and notebook Cell 58 are hand-coded capability matrices |
| Saved logs / result files | **No** | none |
| Ground-truth labels of any kind | **No** | none |

**Experimentally substantiated results: none exist in the repository.** The only verifiable quantitative facts are dataset dimensions and the deterministic behaviours reproduced in this report.

---

## 9. Unsupported or exaggerated claims

| # | Claim | Source | Status |
|---|---|---|---|
| 1 | "enterprise-grade, multi-agent Retrieval-Augmented Generation (RAG) system" | README:10 | No generation; not enterprise-grade (dev server, no auth/persistence); agents are sequential functions |
| 2 | "autonomous" auditing | README title, UI | Deterministic fixed pipeline; no autonomy |
| 3 | Valuation & Discrepancy Detector | README:44 | Not implemented; no benchmark data |
| 4 | Risk & Anomaly Scorer, "composite risk percentiles" | README:45 | Not implemented |
| 5 | Consensus & Reconciliation Auditor, COMPLIANT/FLAGGED/WARNING | README:46 | Not implemented |
| 6 | "TF-IDF Semantic RAG Engine" / "semantic search" | README:34,43 | TF-IDF is lexical, not semantic; no generation |
| 7 | "Dense TF-IDF cosine similarity" | HomePage:537 | TF-IDF vectors are sparse |
| 8 | "Levenshtein distance" matching | HomePage:536 | Not implemented |
| 9 | "cryptographic audit ID" | HomePage:540 | ms-epoch mod 10⁶ |
| 10 | "outputs the final compliance verdict" | HomePage:540 | Report stage outputs no verdict |
| 11 | "240+ international trade policies … multilateral treaties, preferential agreements, quota restrictions" | README:43,116 | 240 identical placeholder records labelled "Prototype" |
| 12 | "1,200+ commodities with … benchmark unit prices" | README:34,114 | 1,200 synthetic variants of 60 types; no prices |
| 13 | "400 commercial shipment invoices with declared values, importer details, and empirical audit status" | README:117 | Synthetic; no declared amounts, importer or status |
| 14 | "processing multi-thousand trade transactions" | README:34 | 400 records; no batch execution of the pipeline |
| 15 | "Detects fraudulent undervaluation" | README:44 | Nothing detects undervaluation; "fraud" cannot be established by such a tool in any case |
| 16 | "200+ jurisdictions" | README:32 | 40 countries |
| 17 | "0 % False Negatives" | SystemBenchmark.jsx:102 | Hard-coded literal, not measured |
| 18 | "37.5 % vs 100 %" capability scores | SystemBenchmark.jsx:84-96 | Count of a hand-picked feature list |
| 19 | "Runs both … side-by-side to benchmark accuracy" | README:189 | No accuracy computed; feature list hard-coded |
| 20 | Notebook contains EDA, anomaly modelling, classification validation | README:246-249 | Not present |
| 21 | Sample request with `declared_value/declared_duty/declared_vat` | README:192-200 | Fields ignored by backend |
| 22 | "AUDIT VERIFIED" / "Verified Active" | AuditConsole.jsx:377,467 | Hard-coded for every result |
| 23 | "Statutory assessable value calculation per WTO customs valuation rules" | HomePage:506 | Simplified price×qty+freight; no WTO valuation method applied |
| 24 | "Datasets/" directory in repo structure | README:208 | Does not exist (loader tolerates it) |

---

## 10. Missing experiments (prioritised)

**Essential (no defensible empirical paper without these):**
- **E1. Independent ground truth.** Construct a labelled evaluation set whose labels are assigned *without* reference to either matcher. For example, product descriptions with realistic variation (synonyms, typos, word order, brand-style names, out-of-catalogue goods) labelled with the correct catalogue entry/HS-6 or "should abstain"; and country strings (aliases, ISO codes, misspellings, unknowns) labelled with the correct jurisdiction or "unknown". Use two annotators plus an agreement statistic (Cohen's κ).
- **E2. Head-to-head evaluation on identical inputs.** Measure agentic vs. baseline on E1:
  - identification accuracy and coverage;
  - **silent-fallback rate** (wrong output without any warning);
  - abstention correctness;
  - jurisdiction-resolution accuracy;
  - landed-cost error against a reference computed from the true labels;
  - paired significance test (McNemar) for accuracy differences.
- **E3. Computational performance.** Repeated in-process and HTTP measurements (warm-up, ≥30 repetitions, mean/median/p95/throughput, batch of 400) with a documented environment.

**Required for the README-style paper (Option B in §11):**
- **E4. Valuation discrepancy.** Requires external unit-value benchmarks per HS-6 (e.g. official trade statistics) and a label definition that is independent of the detector threshold.
- **E5. Declared-vs-recomputed reconciliation.** Requires declared duty/VAT fields. Fault injection would be largely circular, because recomputation trivially detects injected under-declaration above tolerance. In addition, HS codes do not affect duty in the current tariff table, so HS substitution is financially invisible until line-level tariffs exist.
- **E6. Retrieval evaluation.** Requires a real, heterogeneous policy corpus with relevance judgements (P@k, MRR). A comparison of TF-IDF (backend), BM25 and MiniLM dense (notebook) would then be informative.
- **E7. Ablation.** Only meaningful once removing a stage changes outputs. Today, removing retrieval changes nothing financially, and removing the keyword flag changes nothing at all.

**Optional:** threshold sensitivity (once thresholds exist); concurrency/load test with a production WSGI server.

---

## 11. Preliminary contribution and novelty assessment

| Candidate (from brief) | Assessment |
|---|---|
| A. Sequential multi-agent verification architecture | **Not supportable as "multi-agent."** Supportable as a *modular staged pipeline with per-stage provenance*. That is an engineering pattern, not a research novelty. |
| B. Integrated framework: HS validation + tariff + TF-IDF retrieval + valuation + risk + reconciliation | **Only 3 of 6 elements exist**, and none of them performs validation. |
| C. Comparative evaluation vs. single-pass baseline | **Feasible only with new ground truth (E1–E2).** On shipped data the measured difference is exactly zero. A robustness study could show a real and interesting trade-off: higher coverage versus confidently wrong outputs. |
| D. Unified transaction-level decision support over structured trade knowledge | Closest to what exists, but novelty is low: landed-cost/duty calculators and rule-based customs screening are well established. This will be checked against literature in Phase 2. |

**Honest assessment.** In its present form the repository supports, at most, a modest *system-description* paper. A peer-reviewed empirical contribution requires either (A) re-scoping to the implemented system plus a new, independently labelled robustness evaluation, or (B) implementing the README's missing components on real reference data and evaluating them. Writing the paper as the README describes it is not an option: it would describe components and results that do not exist.

**Scope options for the authors:**
- **Option A — re-scope (feasible for a late-Nov/early-Dec 2026 submission).** Working title: *"Staged Versus Single-Pass Rule-Based Pipelines for Customs Landed-Cost Pre-Assessment: A Robustness Study on Product and Jurisdiction Resolution."* Contribution: a traceable staged pipeline; an independently labelled robustness benchmark; an empirical coverage-versus-silent-error trade-off; and latency overhead. Retrieval is described accurately as lexical lookup over a prototype corpus and is not evaluated as RAG.
- **Option B — extend (realistic Jan–Mar 2027).** Add line-level tariffs, valuation benchmarks, a declaration-reconciliation stage, a real policy corpus and a verdict layer. Then run E4–E7 with ablation. This is a stronger paper, but it needs new code (to be integrated into the app by the authors, or clearly scoped as a research prototype) and real external data.

---

## 12. Reference paper structural analysis (benchmark only, not a content source)

*"XAI for Credit Card Fraud: An Ensemble Learning Approach…", ResGenXAI 2025, DOI 10.1109/RESGENXAI64788.2025.11344026.* Word counts are approximate (±15 %) because of two-column text extraction.

| Section | Approx. words | Elements |
|---|---|---|
| Title / 6 author blocks | — | 2 rows × 3 IEEE author blocks |
| Abstract | ~105 | One paragraph, no citations |
| Keywords | 12 terms | (IEEE usually prefers 3–5 Index Terms) |
| I. Introduction | ~240 | 1 citation |
| II. Related Work | ~280 | Thematic paragraphs, 3 citations, gap statement at end |
| III. Methodology | ~390 | 13-step algorithm box; Fig. 1 flowchart; A. Dataset & preprocessing, B. Model training, C. Metrics, D. XAI |
| IV. Experiments & Results | ~300 | Table 1 (7 metrics × 5 models); Figs. 2–3 (ROC, PR) |
| V. Explainability analysis | ~350 | A. SHAP (1 global, 2 local), B. LIME; Figs. 4–9 |
| VI. Conclusion & Future Work | ~200 | No citations |
| References | 12 entries | Only [1]–[3] cited in text; several unrelated (e.g. PCA tutorial, education-fraud case study) |
| **Total** | **≈1,850–2,000 body words, 6 pages, 9 figures, 1 table, 0 equations** | |

Take from it: a 6-page length, the section order (Intro → Related Work → Methodology with algorithm and figure → Results with table → analysis → Conclusion), and one algorithm box. **Do not replicate:** uncited reference-list entries, the low citation density, the 12-term keyword list, or the absence of equations and statistical testing.

---

## 13. Template analysis
- `IEEE-conference-template-062824.tex`, dated 27 Jun 2024; `IEEEtran.cls` V1.8b; `\documentclass[conference]{IEEEtran}`; packages cite, amsmath, algorithmic, graphicx.
- Author blocks via `\IEEEauthorblockN/\IEEEauthorblockA`; there are six slots, so four authors fit as one 4-column row or 2×2. Title/abstract must not contain symbols, footnotes or math.
- No LaTeX engine is installed in this container. One will be installed before compiling in Phase 6.

---

## 14. Timeline feasibility (target: November 2026; today is 14 Nov)

| Task | Option A | Option B |
|---|---|---|
| Author decisions and data provenance answers | 1–2 days | 1–2 days |
| Labelled benchmark construction (two annotators) | 2–3 days | 4–6 days (+ external data collection) |
| New implementation | none (or bug fixes, if authors choose) | 1–2 weeks |
| Experiments | 1 day | 3–5 days |
| Literature review (verified, 20–30 refs) | 3–4 days | 3–4 days |
| Drafting, figures, LaTeX | 3–4 days | 4–5 days |
| Co-author review and revisions | 2–3 days | 3–4 days |
| **Earliest honest submission** | **~30 Nov – 7 Dec 2026** | **~Jan – Feb 2027** |

Option A can meet a late-November or early-December deadline only if the author decisions and annotations arrive within days. Venue deadlines will be verified in the conference shortlist step.

---

## 15. Questions requiring author clarification

1. **Scope:** Option A (re-scope plus robustness study) or Option B (extend implementation)? Or a different direction?
2. **Other code:** Is the README's six-agent design (valuation, risk scoring, consensus, declared-value inputs) implemented anywhere else, such as another branch, a local copy or the deployed application? Only `main` exists on GitHub.
3. **Data provenance:** Who produced `AI_Tax_Auditor_Large_Datasets.zip`, and how (script, spreadsheet, LLM-generated, manual)? What are the sources and reference dates for the VAT, duty and exchange-rate values?
4. **Authorisation:** May I write *new* evaluation code and benchmark files under `research_paper/experiments/` (no changes to the app) and execute the experiments?
5. **Annotation:** Can two authors independently label the evaluation set (about 300–500 items, roughly 2–3 hours each)?
6. **Bug fixes:** Do you want to fix the identified defects (US→Australia, silent HS fallback, missing currencies, whitespace input) *before* evaluation? If so, the paper evaluates the fixed commit, which must be tagged. If not, the paper reports them as findings.
7. **Retriever:** Should the paper describe the backend TF-IDF retriever only, or also the notebook's MiniLM/ChromaDB variant?
8. **Terminology:** Are you willing to use "stage/module" instead of "autonomous agent", or to define "agent" narrowly?
9. **Venue constraints:** Any required venue, page limit, region, budget or registration constraints?
10. **Authorship:** The README lists K. Siddharth Reddy, Syeda Sayeeda Farhath and P. Naga Bhargav. The manuscript metadata lists Syeda Sayeeda Farhath, Siddharth Karanam, P. Naga Bhargav Reddy and Baalne Anjali. Please confirm that "K. Siddharth Reddy" = "Siddharth Karanam" and "P. Naga Bhargav" = "P. Naga Bhargav Reddy", and confirm Baalne Anjali's contribution (she does not appear in the README or the git history).
11. **Contributions, corresponding author, funding:** CRediT roles, corresponding author, and any funding or acknowledgement.
12. **AI-assistance disclosure:** IEEE requires AI-generated content (text, figures, code) to be disclosed in the acknowledgments. Do you agree to include such a statement? Exact policy wording to be verified at submission time.
