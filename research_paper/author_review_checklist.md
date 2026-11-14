# Author Review Checklist (living document)

Status: **Phase 2–3 plans proposed (14 Nov 2026). Awaiting author approval before implementation (Phase 4).**
The manuscript has not been drafted. Nothing is submission-ready.

## A. Decisions resolved
- [x] Scope: **Option A** (narrower empirical evaluation of the existing staged system) — authors, Phase 2 brief
- [x] Authorisation to modify the project on a research branch (no force-push, no `main`) — authors
- [x] Author list, order, names and affiliations (see §C)
- [x] No other implementation exists; README design was aspirational — authors

## B. Decisions required now (see `research_question_and_scope.md`, `experiment_implementation_plan.md` §6)
- [ ] Approve the primary research question, supporting questions and provisional title
- [ ] Approve the exclusion of policy-retrieval *relevance* evaluation (placeholder corpus)
- [ ] Approve S1 design (abstention threshold, ISO alias table, no fuzzy country match)
- [ ] App change C1 (new `backend/lexitax_v2/` package) — yes/no
- [ ] App change C2 (additive `/api/v2/audit` route in `server.py`) — yes/no
- [ ] App change C3 (relabel hard-coded benchmark claims in `SystemBenchmark.jsx`) — yes/no
- [ ] Annotation roles and availability (≈4–5 person-hours total; run the 10-item pilot first)
- [ ] Use of the UN Comtrade-derived HS 2022 file (ODC-PDDL) and pycountry ISO data as reference sources
- [ ] Confirm the canonical repository URL for the paper. The brief says `github.com/K-Siddharth-Reddy/ai-tax-auditor7`; this session's remote is `github.com/K-Siddharth-Reddy-CR7/ai-tax-auditor7`.

## C. Author metadata (authoritative; do not reorder)
1. Syeda Sayeeda Farhath — syedasayeedafarhath@ieee.org
2. Siddharth Karanam — siddharthreddy1908@gmail.com
3. P. Naga Bhargav Reddy — nagabhargavreddy175@gmail.com
4. Baalne Anjali (faculty mentor) — anjali1820@vardhaman.org

Affiliation (all): Department of Computer Science and Engineering, Vardhaman College of Engineering, Hyderabad, India.
README name variants refer to the same people (confirmed by the authors). The README is not changed by this work.

## D. Authorship requirements (IEEE) — to be confirmed per author before submission
Each author must have made an intellectual contribution, taken part in drafting or critically revising the paper, approved the final version including references, and accepted responsibility for it.
- [ ] Author 1: research direction and coordination are recorded. Confirm participation in drafting/revision and final approval.
- [ ] Author 2: implementation is recorded. Confirm review of S1 code and results, drafting/revision, and approval.
- [ ] Author 3: literature survey is recorded. Confirm verification of references and related-work text, and approval.
- [ ] **Author 4: "professional academic guidance" alone may not meet IEEE authorship criteria.** Confirm intellectual input (e.g. research direction or methodology review) and critical revision of the manuscript, and approval. Otherwise consider the acknowledgments instead.
- [ ] Corresponding author: not assumed. Confirm (Author 1 is the coordination contact).
- [ ] Funding: none assumed. Confirm.

## E. AI-assistance disclosure (draft; verify against current IEEE and venue policy)
IEEE requires disclosure, in the acknowledgments, of AI-generated content (text, figures, images, code), naming the AI system and the sections and extent. A truthful draft will cover:
- repository analysis;
- evaluation and S1 code drafting;
- literature discovery;
- text drafting and editing.

The human authors verify all scientific content. No AI system is listed as an author.
- [ ] Authors agree to the disclosure wording (to be drafted with the manuscript)

## F. Claims that must NOT appear unless implemented and measured
Generative RAG; autonomous/multi-agent deliberation; valuation-discrepancy detection; risk scoring/percentiles; consensus verdicts; fraud detection; Levenshtein matching; cryptographic IDs; "0 % false negatives"; 200+ jurisdictions; real customs declarations; real trade policies; legal correctness of tax rates.

## G. Pending phases
- [ ] Phase 4: implementation (after approval)
- [ ] Phase 5: experiments
- [ ] Phase 6: verified literature review; conference shortlist
- [ ] Phase 7: manuscript (≤ 6 pages, compiled and page-checked)
- [ ] Phase 8: three-reviewer QA; `final_submission_checklist.md`
