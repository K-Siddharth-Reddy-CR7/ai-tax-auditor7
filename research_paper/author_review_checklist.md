# Author Review Checklist (living document)

Status (27 Nov 2026): **pilot and P7 reviews completed; joint freeze approval by Authors 1 and 2 recorded in `freeze_approval_record.md`. The freeze itself has NOT been executed** (no `MANIFEST.json`; no tuning or evaluation). Earlier status (15 Nov 2026): human review materials prepared, see `phase7_methodology_decisions.md` §6.
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
- [x] **Pilot (Author 1, sole reviewer):** 10/10 Accept, no comments (reported 23 Nov 2026); see `phase8_pilot_record_and_integrity.md`
- [x] Option A: exclude the 8 inspected TEST items from final metrics. Approved in principle 24 Nov; implemented in Phase B on 26 Nov 2026 (`experiments/evaluation_exclusions_v1.json`)
- [x] Authors confirm the Phase B exclusion list: all authors confirmed the eight pilot TEST exclusions (user statement, 27 Nov 2026); Authors 1 and 2 confirmed them again in the joint freeze approval of 27 Nov 2026 (`freeze_approval_record.md`). The pinned file's own `authorised_by` text is unchanged. A separate confirmation of the file's wording was not reported.
- [x] **P7 review (Author 1):** 16 look-alikes and the 100-name scan, completed. The 4 exclusions were authorised by the user and then reviewed and approved by all four authors (user statement, 26 Nov 2026); recorded in `experiments/pilot/authorised_review_treatments_v1.csv`
- [x] Tuning constraint: strict "SER ≤ SER(B) on DEV" retained; not to be relaxed after results
- [x] External fuzzy-matching baseline: deferred until initial results
- [x] Open Products Facts: licence not established, so withdrawn; replaced by Unicode emoji names (Unicode License v3)
- [x] Approve freezing: joint approval by Author 1 (Syeda Sayeeda Farhath, corresponding author) and Author 2 (Siddharth Karanam), each given independently on 27 Nov 2026, of the package at commit `0e5a831` (code identity `1930a0b2…`); see `freeze_approval_record.md`. **Freeze execution (`run_all.py --stage freeze --approved-by …`) still pending separate authorisation.**
- [ ] 60-item label audit: deferred unless the pilot finds a rule-level problem; catalogue HS plausibility check: optional
- [x] Accept the use of the unofficial HS mirror (UN Comtrade-derived, PDDL) with the stated caveats: the current HS dataset is retained and its unofficial-mirror provenance must be disclosed in the paper (author decision; confirmed by Authors 1 and 2 on 27 Nov 2026, `freeze_approval_record.md`)
- [x] Review the S1 code (`backend/lexitax_v2/`). It was written with AI assistance and must be understood and accepted by the authors, ideally Author 2: Author 2 (Siddharth Karanam) reviewed `backend/lexitax_v2/` and accepted S1 (27 Nov 2026, `freeze_approval_record.md`)

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
- [ ] Author 2: implementation is recorded. Confirm review of S1 code and results, drafting/revision, and approval. (S1 code review confirmed 27 Nov 2026; review of results, drafting/revision and final approval still to be confirmed.)
- [ ] Author 3: literature survey is recorded. Confirm verification of references and related-work text, and approval.
- [ ] **Author 4 will be asked to substantively review and revise the manuscript (authors, 15 Nov 2026). Authorship remains conditional on that review and her final approval.** "Professional academic guidance" alone may not meet IEEE authorship criteria. Confirm intellectual input (e.g. research direction or methodology review) and critical revision of the manuscript, and approval. Otherwise consider the acknowledgments instead.
- [x] Corresponding author: **Author 1 (Syeda Sayeeda Farhath)**, confirmed 15 Nov 2026.
- [x] External funding: **none** (confirmed 15 Nov 2026). No funding acknowledgement.

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
- [ ] Phase 5: experiments (pilot complete; freeze approved 27 Nov 2026; blocked on freeze execution)
- [ ] Phase 6: verified literature review; conference shortlist
- [ ] Phase 7: manuscript (≤ 6 pages, compiled and page-checked)
- [ ] Phase 8: three-reviewer QA; `final_submission_checklist.md`
