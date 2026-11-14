# Author Review Checklist (living document)

Status: **Phase 1 complete. Awaiting author decisions before Phases 2–7.**
The manuscript is **not** submission-ready and has not been drafted.

## A. Decisions required now
- [ ] Scope: Option A (re-scope plus robustness study) / Option B (extend implementation) / other (`repository_investigation.md` §11)
- [ ] Authorisation to create `research_paper/experiments/` and run new experiments
- [ ] Bug fixes before evaluation? If yes, tag the evaluated commit
- [ ] Two annotators available for the labelled benchmark
- [ ] Terminology: "stage/module" vs. narrowly defined "agent"
- [ ] Retriever(s) to describe: backend TF-IDF only / plus notebook MiniLM

## B. Data provenance (needed for the Dataset section)
- [ ] How `AI_Tax_Auditor_Large_Datasets.zip` was produced (script / LLM / manual)
- [ ] Source and reference date for VAT rates, duty rates and exchange rates
- [ ] Confirmation that all records are synthetic prototype data

## C. Author metadata (manuscript order is authoritative; do not reorder)
1. Syeda Sayeeda Farhath — syedasayeedafarhath@ieee.org
2. Siddharth Karanam — siddharthreddy1908@gmail.com
3. P. Naga Bhargav Reddy — nagabhargavreddy175@gmail.com
4. Baalne Anjali — anjali1820@vardhaman.org
Affiliation (all): Dept. of CSE, Vardhaman College of Engineering, Hyderabad, India

- [ ] **README discrepancy:** README lists K. Siddharth Reddy, Syeda Sayeeda Farhath, P. Naga Bhargav (three authors, different order and names). Confirm the name mappings and Baalne Anjali's inclusion. Decide whether to update the README (not changed by this work).
- [ ] Each author's actual contributions (CRediT), without inference from author order
- [ ] Corresponding author
- [ ] Funding / acknowledgements (none assumed)
- [ ] AI-assistance disclosure statement (IEEE policy; verify current wording)
- [ ] All authors approve the final manuscript and the author order

## D. Claims that must NOT appear in the manuscript unless implemented and measured
Generative RAG; autonomous/multi-agent deliberation; valuation-discrepancy detection; risk percentiles; consensus verdicts; fraud detection; Levenshtein matching; cryptographic IDs; "0 % false negatives"; 200+ jurisdictions; real customs declarations; real trade policies. Full list: `repository_investigation.md` §9.

## E. Pending phases
- [ ] Phase 2: verified literature review (20–30 refs), research gap, `research_gap_and_contributions.md`
- [ ] Conference shortlist with verified deadlines, proceedings, Scopus evidence and fees
- [ ] Phase 3–4: `experimental_evaluation_plan.md`, experiments executed, results
- [ ] Phase 5–6: `ieee_research_paper.md`, `.tex`, `references.bib`, `figures/`
- [ ] Phase 7: three-reviewer critique and revisions
