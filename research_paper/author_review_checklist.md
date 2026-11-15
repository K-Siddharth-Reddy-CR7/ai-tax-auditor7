# Author Review Checklist (living document)

Status: **Phase 6 pre-evaluation audit complete (15 Nov 2026). Ready for pilot review; NOT ready for freeze.** See `pre_evaluation_methodology_audit.md` §6.
The manuscript has not been drafted. Nothing is submission-ready.

## A. Decisions resolved
- [x] Scope: **Option A** (narrower empirical evaluation of the existing staged system) — authors, Phase 2 brief
- [x] Authorisation to modify the project on a research branch (no force-push, no `main`) — authors
- [x] Author list, order, names and affiliations (see §C)
- [x] No other implementation exists; README design was aspirational — authors

## B. Decisions — resolved on 14 Nov 2026 and still open
- [x] Research question and provisional title approved
- [x] C1 approved and implemented; C2 deferred; C3 approved and implemented
- [x] Canonical repository URL confirmed by the authors: `https://github.com/K-Siddharth-Reddy-CR7/ai-tax-auditor7`
- [ ] **Pilot:** one reviewer (proposed: Author 1) completes `experiments/pilot/pilot_review_sheet.csv` (≈ 15–20 min); see `experiments/pilot_review_sheet.md`
- [ ] **Look-alike confirmation:** same reviewer completes `experiments/pilot/p7_lookalike_confirmation.csv` (≈ 15–20 min), or the authors decide to drop the 60 look-alikes
- [ ] Tuning constraint: keep "SER ≤ SER(B) on DEV" or set an explicit tolerance
- [ ] Optional external fuzzy-matching baseline B2: yes/no
- [ ] Accept the Open Products Facts licence caveat (or request an alternative source)
- [ ] Approve freezing: `run_all.py --stage freeze --approved-by NAME`
- [ ] 60-item label audit: deferred unless the pilot finds a rule-level problem; catalogue HS plausibility check: optional
- [ ] Accept the use of the unofficial HS mirror (UN Comtrade-derived, PDDL) with the stated caveats, or supply WCO/UN source files
- [ ] Review the S1 code (`backend/lexitax_v2/`). It was written with AI assistance and must be understood and accepted by the authors, ideally Author 2

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
- [ ] Corresponding author: Author 1 proposed by the authors, **pending final confirmation**.
- [ ] Funding: unconfirmed. No funding statement will be written until confirmed.

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
- [x] Phase 4: implementation (S1, tests, evaluation infrastructure, C3)
- [ ] Phase 5: experiments (blocked on pilot/freeze)
- [ ] Phase 6: verified literature review; conference shortlist
- [ ] Phase 7: manuscript (≤ 6 pages, compiled and page-checked)
- [ ] Phase 8: three-reviewer QA; `final_submission_checklist.md`
