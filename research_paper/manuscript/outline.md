# Manuscript outline (planning only, 26 Nov 2026)

**Working title:** Silent Errors versus Safe Abstention in Staged Customs Pre-Assessment: An Empirical Study of Product and Jurisdiction Resolution

**Authors (fixed order):**
1. Syeda Sayeeda Farhath (corresponding author)
2. Siddharth Karanam
3. P. Naga Bhargav Reddy
4. Baalne Anjali (faculty mentor; authorship conditional, see `../author_review_checklist.md` §D)

Affiliation of all authors: Dept. of CSE, Vardhaman College of Engineering, Hyderabad, India.

**Legend:**
- **S1:** draftable before results (Stage 1).
- **S2:** results-dependent (Stage 2).
- **[CONFIRM]:** needs author confirmation.
- **[RESULT]:** placeholder until the audited results exist.

Page target: about six IEEE two-column pages, subject to the selected venue's template. Essential methods are not to be cut merely to fit.

| # | Section | Stage | Evidence sources (repository) | Placeholders / open points |
|---|---|---|---|---|
| — | Abstract | S2 | Final results only | [RESULT] all findings |
| — | Keywords | S1 | — | [CONFIRM] keyword list |
| 1 | Introduction | S1 (final paragraph S2) | `research_question_and_scope.md`, `repository_investigation.md` | Motivation: silent defaults and fabricated codes in assistive pre-assessment. [RESULT] summary of findings |
| 2 | Related work | S1 | `literature_review.md` (strategy, unverified leads) → verified `references.bib` | Areas: entity resolution and product matching; ambiguous product identification; hierarchical classification; abstention and selective prediction; calibration; pipeline error propagation; HS-code and customs classification; risk-aware automation; evaluation for imbalanced or clustered data. Direct precedents are distinguished from background |
| 3 | Research questions and contributions | S1 | `research_question_and_scope.md`; `RESEARCH_STATE.md` §1 | Contributions claimed only if the results support them |
| 4 | System architecture and methodology | S1 | `backend/server.py` (B, S0), `backend/lexitax_v2/` (S1), `lexeval/systems.py` (ladder L0–L5), `RESEARCH_STATE.md` §2 | Accurate description: fixed six-stage sequential pipeline; no LLM; TF-IDF retrieval prototype; S1 evidence tiers; abstention; no confidence score |
| 5 | Dataset construction and annotation | S1 (counts final after Phase D) | `lexeval/build_*.py`, `config.json`, `data_provenance.md`, `dataset_sampling_rationale.md`, `pilot_review_sheet.md`, `p7_review_sheet.md`, `phase8_pilot_record_and_integrity.md`, `pilot/authorised_review_treatments_v1.csv`, `evaluation_exclusions_v1.json` | P1–P8 and J1–J7; label sources; group split 30/70 DEV/TEST (seed 20261114); the 10-item pilot; the P7 review; 4 review exclusions; 8 evaluation exclusions. [RESULT-like] final counts after the Phase D rebuild |
| 6 | Experimental setup and metrics | S1 | `scoring.py`, `stats.py`, `evaluate.py`, `tuning.py`, `config.json` (`tuning_rule`, `statistics`), `latency.py` | Outcome taxonomy; coverage, decision accuracy, silent-error rate; cluster bootstrap, cluster permutation test, Holm over 18 tests, McNemar (secondary); strict DEV tuning rule; latency protocol (Phase C) |
| 7 | Results and analysis | S2 | `experiments/results/` (after the authorised evaluation) | [RESULT] tables of coverage versus silent error for B, S0 and S1; ladder attribution; negative or inconclusive outcomes reported |
| 8 | Error propagation and sensitivity | S2 | Propagation classes in `evaluate.py`; sibling sensitivity outputs | [RESULT] propagation into duty, VAT and landed cost; sibling sensitivity reported separately |
| 9 | Discussion | S2 | — | Interpretation limited to the experiments |
| 10 | Limitations and threats to validity | S1 | `RESEARCH_STATE.md` §11; `author_review_checklist.md` §F | Synthetic data; unsourced tax rates; placeholder policies; unofficial HS mirror; unverified catalogue HS codes; same-team design; single pilot reviewer; latency on a shared VM |
| 11 | Conclusion and future work | S2 | — | [RESULT] |
| — | Acknowledgments and AI-use disclosure | S1 → S2 | `RESEARCH_STATE.md` §12 | [CONFIRM] venue AI policy and wording; no funding |
| — | References | S1 | `references.bib` (verified only) | — |
