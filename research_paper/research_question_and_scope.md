# Research Question and Scope (Phase 2 — proposed, awaiting author approval)

Status: **PROPOSED.** Nothing here is a result. Titles and gap statements are provisional until the literature review (Phase 6) is complete.

## 1. What the paper is about

LEXITAX AUDIT pre-assesses an import transaction. It identifies the product (catalogue entry → HS-6 code), resolves the destination jurisdiction, applies that jurisdiction's duty and VAT/GST rates, computes the landed cost, and attaches a policy record. Every downstream number depends on two **resolution** steps: *product resolution* and *jurisdiction resolution*. Phase 1 showed that the existing staged pipeline resolves more free-text inputs than the single-pass baseline. It does so partly by **guessing silently**: fabricated HS code 8471.30 for unknown goods, "US" → Australia, "Car" → Memory Card. A decision-support tool that is confidently wrong is more dangerous to an auditor than one that says "I cannot resolve this".

The paper therefore studies **coverage versus silent error** in staged customs pre-assessment. It compares a strict single-pass baseline, the original heuristic staged pipeline, and a refined staged pipeline that resolves against authoritative reference data and **abstains** when evidence is weak. It also measures how resolution errors **propagate** (or are masked) in duty, VAT and landed-cost outputs.

This is an *assistive decision-support* study. No component makes, or is evaluated as making, a legally authoritative classification, valuation or compliance determination.

## 2. Primary research question

**RQ.** In a staged, rule-based customs pre-assessment pipeline, how do alternative product- and jurisdiction-resolution strategies trade off coverage against silent (unflagged) errors, and how do those errors propagate into duty, VAT and landed-cost outputs?

The strategies are:
1. strict single-pass matching;
2. heuristic multi-tier fallback;
3. reference-data resolution with threshold-based abstention.

## 3. Supporting questions and hypotheses

| ID | Question | Hypothesis (to be tested, may be rejected) |
|---|---|---|
| SQ1 | How accurately do the three systems resolve product descriptions to HS-6 codes, and how often do they answer wrongly instead of abstaining on unsupported goods? | H1a: S0 has higher coverage than B on in-catalogue variants. H1b: S0 has a higher silent-error rate than B on unsupported goods. H1c: S1 lowers the silent-error rate relative to S0, at a measurable coverage cost. |
| SQ2 | Same questions for jurisdiction strings (names, ISO codes, aliases, typos, unsupported and ambiguous countries). | H2: S0's substring rule produces real-country confusions (e.g. Niger→Nigeria), and S1's alias-plus-abstain design removes them without reducing coverage on ISO-form inputs. |
| SQ3 | What share of end-to-end transactions return a wrong duty/VAT/landed cost without warning, how large is the error, and which stage causes it? | H3: Because duty depends only on the destination, product errors are *financially masked* (zero cost error, wrong HS), while jurisdiction errors cause cost deviations. This is a structural property, which we quantify rather than "discover". |
| SQ4 | What latency and throughput overhead do staging and abstention add? | H4: All systems stay well under 1 ms per transaction in-process. The overhead is real but operationally negligible. |
| SQ5 | Which components cause the observed differences? | Answered by single-variable ablation (see the evaluation plan). |

## 4. Systems under comparison

- **B — original single-pass baseline:** `run_normal_auditor_pipeline`, unchanged.
- **S0 — original staged pipeline:** `run_agentic_auditor_pipeline`, unchanged.
- **S1 — refined staged pipeline (new research implementation):**
  - validated inputs;
  - product resolution by normalised exact match, then character-trigram TF-IDF similarity with a single abstention threshold tuned on a development split;
  - jurisdiction resolution by exact match plus an ISO 3166-1 alias table, with explicit "unsupported"/"unresolved" outcomes and no fuzzy matching by default;
  - no fabricated defaults;
  - the **same** tax tables, arithmetic and policy retriever as S0, so that differences are attributable to resolution.

## 5. Proposed title (provisional)

> **Silent Errors versus Safe Abstention in Staged Customs Pre-Assessment: An Empirical Study of Product and Jurisdiction Resolution**

Alternatives:
- "Coverage, Abstention and Error Propagation in a Staged Customs Landed-Cost Pre-Assessment Pipeline"
- "When Fallbacks Fail Silently: Evaluating Resolution Strategies for Automated Customs Pre-Assessment"

The final choice comes after the literature review. No title will use "multi-agent", "autonomous", "RAG" or "fraud".

## 6. Research gap (provisional, to be verified in Phase 6)

From preliminary search (not yet verified):
- HS-code prediction from product text is an active area, mostly framed as maximising accuracy with ML/NLP models.
- Customs fraud/risk work (e.g. transaction-level fraud detection) targets selection of declarations for inspection.
- Selective classification / reject-option theory (Chow, 1970, and later work) formalises the error–reject trade-off.

The gap we expect to substantiate is that **evaluations of customs-assistance pipelines rarely report silent-error behaviour, abstention, or cross-stage error propagation into financial outputs.** They report accuracy of an isolated classifier. This paper will not claim to be the first study of anything unless the review supports it.

## 7. Contributions (to be claimed only if results support them)

1. A reproducible, open evaluation benchmark for product and jurisdiction resolution in customs pre-assessment. Labels come from authoritative references (HS 2022 subheading descriptions; ISO 3166-1), controlled perturbations, and independently double-annotated human-written descriptions. All labels are independent of the evaluated systems.
2. A comparative study of three resolution strategies, measuring coverage, accuracy, silent-error rate, risk–coverage behaviour and statistical significance with paired tests.
3. An error-propagation analysis showing which resolution errors reach financial outputs and which are masked.
4. A refined, traceable staged pipeline (S1) with explicit abstention, released alongside the original implementation, plus a corrected record of the original system's limitations.

## 8. Scope and exclusions

**In scope:** product → HS-6 resolution at catalogue level; jurisdiction resolution over the 40 supported countries; end-to-end propagation into the system's own duty/VAT/landed-cost outputs; latency/throughput; ablation.

**Excluded, and stated in the paper:**
- **Legal correctness of tax rates.** Rates come from the project's prototype table (unsourced; EU rates internally inconsistent). Correctness is measured *relative to the system's own reference tables*.
- **Policy-retrieval quality.** The 240 policy records are identical placeholders, so relevance metrics would be meaningless. Retrieval is described as a lexical lookup, and its structural behaviour is reported in one paragraph. A real-corpus evaluation is future work.
- Valuation-discrepancy detection, risk scoring and consensus. These were never implemented and are not added.
- Fraud detection, generative AI, LLMs and multi-agent claims.
- Real customs declarations. None are used, and the synthetic transactions supply only numeric fields.

## 9. Feasibility within six pages

| Block | Budget |
|---|---|
| Title, authors, abstract, index terms | 0.45 p |
| I Introduction | 0.6 p |
| II Related work (with comparison table if space allows) | 0.7 p |
| III System and methodology (Fig. 1 architecture, resolution rules, equations, algorithm box) | 1.1 p |
| IV Benchmark and setup (Table I datasets) | 0.7 p |
| V Results and discussion (Table II main results, Fig. 2 risk–coverage, Table III propagation and ablation) | 1.3 p |
| VI Limitations / threats to validity | 0.3 p |
| VII Conclusion | 0.2 p |
| References (~22–25) and acknowledgments with AI disclosure | 0.65 p |
| **Total** | **6.0 p** |
