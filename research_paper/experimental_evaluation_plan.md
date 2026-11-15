# Experimental Evaluation Plan — v2, amended by v3 (15 Nov 2026)

> **v3 amendments (Phase 6 audit). These take precedence over the v2 text below:**
> - **Product benchmark** redesigned into eight categories P1–P8 (855 items). See `experiments/dataset_sampling_rationale.md`. §3.2's subsets PA–PE and its counts are superseded.
> - **Country benchmark** subsets are renamed J1–J7. Each item carries `form` and `s1_builtin`. Pooled country claims use held-out forms (J4–J7) only. Supersedes §3.3 naming.
> - **Split** is now 30 % DEV / 70 % TEST (supersedes 40/60).
> - **Statistics:** primary inference uses cluster bootstrap CIs and a cluster-level sign-flip permutation test with Holm correction. Item-level Wilson and McNemar are reported as secondary. Supersedes §5.5.
> - **New outcome rule:** EITHER, for short forms (P4). Answering correctly or abstaining are both acceptable; a wrong code is a silent error.
> - **Pooled scope:** pooled product metrics exclude P8 (formal HS texts, reported separately). The tuning objective excludes P1 and P8.
> - **Latency** times the systems' own entry points, not the evaluation adapters.
> - **Human verification:** a one-reviewer pilot plus look-alike confirmation (`experiments/pilot_review_sheet.md`). The 60-item audit is deferred.
> - Full audit: `pre_evaluation_methodology_audit.md`.

Status: **protocol final pending pilot sign-off.**
- Benchmarks are built as a **DRAFT** and validated (0 errors), but **not frozen**.
- **No evaluation has been run. No numbers in this file are results.**
- The code enforces the gating: `tune`/`evaluate` refuse to run without a frozen manifest carrying a named approver.

This version replaces v1. It incorporates the authors' methodological corrections (1–6) and minimises human annotation.

---

## 1. Systems and exactly how they differ
| | B — original single-step | S0 — original staged | S1 — corrected staged (`backend/lexitax_v2`) |
|---|---|---|---|
| Code | `run_normal_auditor_pipeline` (unchanged) | `run_agentic_auditor_pipeline` (unchanged) | new package; reuses original tables, `calculation_agent`, `PolicyRetriever` |
| Input validation | numeric cast only | numeric cast; empty-string check before strip | explicit rejection: blank text, price ≤ 0, non-finite, non-integer quantity, negative freight |
| Product resolution | first catalogue name containing the input (substring); else **"N/A"** | exact/prefix → substring → max word overlap; else **fabricated 8471.30 "Electronics"** | T1 exact name; T2 whole-token containment with maximality, HS-uniqueness and evidence-coverage rule; T3 bounded-typo containment; else **abstain** |
| Confidence score | none | none (the overlap count is internal and never returned) | **none.** Abstention is decided by deterministic evidence rules, not by a score |
| Country identification | exact table name | exact table name → **bidirectional substring** ("US"→Australia) | ISO 3166-1 aliases (alpha-2/3, name, official, common) + table names, exact after normalisation; no fuzzy match (ablation only) |
| Tax-data availability | unknown → default 5 %/10 % silently | unknown → default 5 %/10 % USD silently | identified-but-unsupported → explicit refusal; unresolved → explicit refusal |
| Missing FX rate | not computed | silently 1.0 | `null` plus flag |
| Costs for unresolved product | computed (product does not enter the formula) | computed (with fabricated HS) | not computed (the product is required, because duty is HS-dependent in reality) |
| Arithmetic, tax table, policy retriever | original | original | **identical original functions** |

**Confidence (correction 3).** Inspection shows that the original implementation produces **no product-classification confidence score**. `relevance_score` exists only for policy retrieval, and it is a TF-IDF score plus fixed bonuses. Nothing can be calibrated. S1 therefore uses measurable properties only:
- exact versus normalised match;
- whether the matched name is fully contained in the input;
- uniqueness of the implied HS-6 code;
- evidence coverage = |tokens of the matched base-type names| / |input tokens|;
- edit distance per token;
- supported versus unsupported jurisdiction;
- availability of tax data.

S1 has three tunable parameters: coverage threshold, maximum typo edits, and minimum token length for typo tolerance. They are selected **on DEV only** by a pre-declared rule (§6).

## 2. Attribution of differences (correction 6): one-change-per-step ladder
Each step changes exactly one component. Equivalence is verified by test: L0 ≡ S0 and L5 ≡ S1, both on all 400 canonical transactions and on DEV benchmark inputs.

| Step | Component changed | What it isolates |
|---|---|---|
| L0 | — (= S0) | reference |
| L1 | + input validation | validation |
| L2 | + ISO country identification (unresolved/unsupported still receive S0's default rates) | country normalisation |
| L3 | + refusal when tax data is unavailable; no FX substitution | tax-data availability |
| L4 | + product abstention instead of the fabricated HS fallback; costs gated on product | abstention |
| L5 | + S1 product evidence tiers (= S1) | product matching |

Extra single-variable ablations:
- S0 − word-overlap tier;
- S0 − partial country match;
- S1 − coverage guard;
- S1 − typo tier;
- S1 + country typo tolerance.

The tax tables, arithmetic and datasets are identical for every variant (correction 6).

## 3. Ground truth (corrections 1, 2, 5)
All labels come from **external reference data or pre-declared deterministic rules**. None comes from any system's output, and none is a model-generated suggestion.

### 3.1 Reference data and provenance
Full details: `experiments/data/external/PROVENANCE.md`.
- **HS 2022 subheading texts.**
  - Source: GitHub `datasets/harmonized-system` @ `b1be3f2`, ODC-PDDL. Converted from the UN Comtrade API.
  - This is an **unofficial mirror**: abridged UN texts, not WCO legal text.
  - Edition confirmed programmatically: codes new in 2022 are present and codes deleted in 2022 are absent. 5,613 six-digit rows = 5,612 WCO subheadings + 1 Comtrade placeholder (WCO total to be checked on WCO's own page).
  - 9 codes with duplicated descriptions and the placeholder are excluded by rule.
- **ISO 3166-1:** `pycountry` 26.2.16, which bundles Debian iso-codes (249 countries). An open re-publication, not the ISO OBP.
- **CLDR 47** localised names via `babel` 2.18.0, locales de/fr/es/it/nl/pt.

### 3.2 Product benchmark (draft counts)
Every item records whether the code exists, the mapping basis, whether the code is in the supported catalogue, and the expected behaviour.

| Subset | Items (draft) | Text source | Expected | Label provenance | Does the description correspond to the code? |
|---|---|---|---|---|---|
| PA | 400 | 60 catalogue base-type names: plain, one full variant name, and 5 surface perturbations (case, whitespace/punctuation, one-edit typo, plural, reorder) | ANSWER catalogue HS-6 | `catalogue_asserted` | **Not verified.** Correctness means "resolved to the right catalogue record". All 43 codes exist in HS 2022, but *mapping plausibility* is unverified; human check optional (§7) |
| PB | 128 | HS 2022 text of the 43 catalogue codes, plus case and one-edit typo | ANSWER that code | `nomenclature_definition` | Yes, by definition: the text is that code's own description |
| PC | 884 | HS 2022 texts of every other subheading in chapters 84/85/94/95 | ABSTAIN (unsupported subheading) | nomenclature | Supported at 6 digits? **No**, so any answer is a wrong HS-6 |
| PD | 4,676 | HS 2022 texts of all subheadings in other chapters (full population, no sampling) | ABSTAIN (outside catalogue) | nomenclature | — |
| PE | 8 | Catalogue tokens shared by base types with ≥ 2 different HS codes (e.g. "Drive", "Card", "Oven") | ABSTAIN (ambiguous) | pre-declared rule | Ambiguity defined before evaluation |

**Pre-declared rules:**
- A perturbation is discarded if it collides with another catalogue name.
- Texts whose normalised form carries conflicting labels are removed (3 removed).
- Exact duplicates are removed (126).

### 3.3 Country benchmark (draft counts)
Identification label (`expected_iso`) and tax-data availability are **separate fields** (correction 2).

| Subset | Items | Source | Identification label | Tax-data availability |
|---|---|---|---|---|
| CA | 120 | 40 table names + case and whitespace noise | ISO | available |
| CB | 884 | ISO forms of all 249 countries | ISO | available for 40; otherwise unavailable → REFUSE |
| CC | 247 | one-edit typo per country (discarded if it equals any alias) | ISO (by construction) | as above |
| CD | 821 | CLDR names, **held out** from S1's alias table (cross-country collisions removed) | ISO | as above |
| CE | 16 | tokens in ≥ 2 ISO names that are not themselves aliases (e.g. "Korea", "South", "Virgin") | none (ambiguous) | REFUSE |
| CF | 34 | CLDR non-country regions (e.g. "Europe", "Caribbean") | none | REFUSE |

**Leakage note.** S1's alias table *is* ISO 3166-1, so S1 is expected to solve CB by construction. CB is reported separately and never presented as generalisation. CC, CD, CE and CF are not derived from S1's table.

### 3.4 Malformed-input set M
18 items with fixed defects (blank text, negative/zero/NaN/∞/text price, zero/negative/fractional/text quantity, negative/NaN/text freight). Expected outcome: explicit rejection.

## 4. Splits and leakage prevention (correction 5)
- Group-level deterministic split, 40 % DEV / 60 % TEST, seed 20261114.
  - Product groups = **HS-4 heading**: catalogue variants, HS texts of the same heading and unsupported siblings never straddle the split.
  - Country groups = ISO code.
  - Ambiguous tokens are grouped by their singular form.
- Validation (draft): 0 identical normalised texts across splits; 0 groups straddling splits; 0 label conflicts.
- Near-duplicates (token Jaccard ≥ 0.9, ≤ 12 tokens): 11 product and 1 country test items have a DEV neighbour. These are reported, not removed, as declared.
- The 1,200 random transaction combinations of v1 are **dropped**, because random pairing would duplicate items and create artificial patterns. Instead there are two controlled propagation runs (§5.4), each varying only one input. The numeric fields cycle deterministically through the 400 synthetic transactions; they affect absolute amounts only, not which errors occur.

## 5. Tasks, outcomes and metrics
### 5.1 Outcome taxonomy (fixed in `lexeval/scoring.py`)
| Outcome | Meaning |
|---|---|
| CORRECT | answered with the labelled value |
| SAFE_ABSTENTION | declined, and declining was expected |
| OVER_ABSTENTION | declined, but an answer was expected |
| EXPLICIT_FAILURE | error or rejection message |
| **SILENT_ERROR** | a wrong value presented as an answer, including fabricated HS codes and default tax rates |

### 5.2 Exact definitions
- **Coverage** = (CORRECT + SILENT_ERROR) / N, the share of items for which an answer is shown.
- **Decision accuracy** = (CORRECT + SAFE_ABSTENTION) / N.
- **Silent-error rate (SER)** = SILENT_ERROR / N (primary safety metric).
- **Selective accuracy** = CORRECT / answered.
- **Selective risk** = SILENT_ERROR / answered.
- All metrics are reported per subset and pooled; the main tables use subset-level figures, because pooled figures are dominated by PD.

### 5.3 Three separate tasks
1. **Product (HS-6)**, with the country fixed to a canonical supported table name.
2. **Country identification.** Correct = right ISO code, regardless of tax data. For B and S0, "identified" means matched to a table country. They cannot identify the 209 unsupported countries by design, which is reported as over-abstention, not error, unless they map to a wrong country (e.g. Niger→Nigeria).
3. **Tax-data behaviour.**
   - Labelled jurisdiction has tax data → expected COMPUTE with its rates. Computing with other rates = SILENT_ERROR, subtyped `default_rates` or `other_country_rates`. Refusing = OVER_ABSTENTION.
   - No tax data → expected REFUSE.
   - Correct rates obtained via a wrong country are counted CORRECT for this task but flagged `correct_rates_wrong_or_no_country` (masked).

### 5.4 Error propagation (correction 4)
The dependency graph was read from code, and will be *measured* rather than assumed:
- Product → HS, category → policy query. The product does **not** enter `calculation_agent`.
- Destination → duty, VAT, currency → landed cost and local cost. In S0 the policy query uses the **raw destination string**.

Two runs:
- **Product run:** product varies; country fixed to canonical. **Country run:** country varies; product fixed to canonical.

Per item and system, each run is classified as one of:
- NO_ERROR;
- MASKED (identification wrong, financial outputs equal to reference), flagged or silent;
- FINANCIAL_ERROR (landed cost differs), flagged or silent, with relative error |L−L*|/L*;
- COMPUTED_WHEN_SHOULD_REFUSE, flagged or silent;
- OVER_REFUSAL;
- EXPLICIT_REFUSAL.

Policy-record mismatches are counted separately. Reference values come from the original arithmetic applied to the labelled jurisdiction's table rates. They are correct **relative to the project's own tables**, not to law.

### 5.5 Statistics
- **Wilson 95 % CIs** for every proportion.
- **Primary family:** exact McNemar tests on paired per-item indicators (decision-correct, silent-error) for B–S0, S0–S1 and B–S1, across the three tasks. That is 18 tests, with **Holm–Bonferroni** correction.
- **Secondary (exploratory, separate family):** adjacent ladder steps.
- Effect size: difference in proportions.
- Latency: median with bootstrap CI over repetition medians.
- No significance claim outside these tests.

## 6. Parameter selection (DEV only)
- Grid: coverage ∈ {0, .25, .34, .5, .67, .75, 1}; typo edits ∈ {0, 1, 2}; minimum length ∈ {4, 5, 6}.
- **Rule (fixed in `config.json`):** maximise DEV macro decision-accuracy over product subsets, subject to DEV macro SER ≤ that of B on DEV.
  - If no configuration satisfies this, minimise macro SER.
  - Ties go to the more conservative configuration.
- The test-set risk–coverage scatter over the grid is reported only as sensitivity analysis.

## 7. Human verification (minimised; see `annotation_guidelines.md`)
- **Mandatory:** a 10-item pilot reviewed independently by two authors, about 15–20 min each. Reviewers check the labelling rules, not system outputs.
- **Recommended:** a 60-item stratified label audit (one reviewer, about 45–60 min) to estimate the label-error rate with a CI.
- **Optional:** plausibility check of the 60 catalogue HS assignments (about 45–60 min).

## 8. Computational performance
- Workload: 1,000 TEST product items with canonical countries. 200 warm-up calls, then 30 repetitions per system, timed in-process with `perf_counter_ns`.
- Recorded environment: CPU model, cores, memory, OS, Python and package versions.
- Results are indicative for a shared cloud VM.

## 9. Limitations to carry into the paper
- **PA labels:** catalogue-asserted mappings, not verified HS classification.
- **HS texts:** abridged, formal language unlike invoice text. There are no real declarations.
- **Perturbations:** synthetic, and may not match real error distributions.
- **Small subsets:** PE (8) and CE (16), so wide CIs.
- **S1 alias table versus CB:** S1 uses the same ISO table as CB, so CB is solved by construction.
- **Tax rates:** unsourced prototype values (EU rates internally inconsistent), so financial correctness is relative to the project tables.
- **Policy corpus:** placeholder text, so retrieval relevance is not evaluated.
- **Scope:** results do not generalise beyond 60 product types and 40 jurisdictions.
- **Authorship of benchmark and systems:** the authors (with AI assistance) built both the systems and the benchmark generator.
