# Research Question and Scope (Phase 2 — proposed, awaiting author approval)

Status: **APPROVED by the authors (Option A), updated 14 Nov 2026 with methodological corrections.** Nothing here is a result. Title and gap statement remain provisional until the literature review (Phase 6).

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
| SQ2 | How accurately do the systems **identify** destination countries (names, ISO codes, held-out CLDR names, typos, ambiguous and non-country strings), and, *separately*, do they compute only when tax data exist and refuse otherwise? | H2: S0's substring rule causes wrong-country identifications, and all original systems apply default rates silently. S1 refuses explicitly, but abstains on typos and held-out aliases (coverage cost). |
| SQ3 | Which resolution errors change downstream outputs (duty, VAT, landed cost, policy record), which are masked, which cause explicit refusal, and which remain undetected? | Measured, not assumed. The code reading suggests that product errors do not alter landed cost and that some wrong-country errors are also financially masked (countries with equal rates). Both are tested in controlled propagation runs. |
| SQ4 | What latency and throughput overhead do staging and abstention add? | H4: All systems stay well under 1 ms per transaction in-process. The overhead is real but operationally negligible. |
| SQ5 | Which components cause the observed differences? | Answered by single-variable ablation (see the evaluation plan). |

## 4. Systems under comparison
- **B:** original single-step baseline (unchanged).
- **S0:** original staged pipeline (unchanged).
- **S1:** `backend/lexitax_v2` (new).

Exact differences, the confidence/abstention design and the one-change-per-step attribution ladder L0→L5 are specified in `experimental_evaluation_plan.md` §1–2.

The original code produces no classification confidence score. S1 therefore abstains on deterministic, measurable evidence (exact/normalised match, whole-token containment, HS-uniqueness, evidence coverage, bounded edit distance, jurisdiction support, tax-data availability), not on an invented score.

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

1. A reproducible, open benchmark for product and jurisdiction resolution in customs pre-assessment. Labels are derived from reference data (HS 2022 texts via a documented UN Comtrade-derived mirror; ISO 3166-1; CLDR 47) and from pre-declared rules. Labels are independent of the evaluated systems and human-checked on a pilot (and an audit sample, if done).
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
- Legal correctness of the catalogue's HS assignments. These are reported as catalogue-asserted; an optional human plausibility check is offered.
- Sub-national destinations (e.g. ISO 3166-2 subdivisions) are out of scope.

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
