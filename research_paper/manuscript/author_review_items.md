# Author questionnaire: unresolved decisions before submission

**Manuscript:** "Silent Errors versus Safe Abstention in Staged Customs Pre-Assessment: An Empirical Study of Product
and Jurisdiction Resolution" (`main.tex` / `main.pdf`, draft of 27 Nov 2026).

**Status: DRAFT FOR AUTHOR REVIEW. Not submission-ready. Nothing has been submitted.** This questionnaire does not
answer any question on the authors' behalf.

Each question has:
- **Recorded:** what the project records already establish, with the file;
- **Needs:** what still requires a decision or confirmation;
- **Who:** the author or authors who must answer;
- **Blocks submission:** Yes or No;
- where justified, a **suggested default**, which is only a suggestion.

Authors: A1 = Syeda Sayeeda Farhath (corresponding author), A2 = Siddharth Karanam, A3 = P. Naga Bhargav Reddy, A4 =
Baalne Anjali.

---

## A. Target conference and submission requirements

**Q1. Which conference will the paper be submitted to?**
- **Context:** the draft uses the generic IEEEtran conference template because no venue has been chosen. The
  unverified leads in `../conference_shortlist.md` (e.g. INDIACom-2027, IC3AI-2027, IEEE CONECCT 2027) were gathered
  on 14 Nov 2026 and none has been checked on an official site.
- **Why it matters:** the venue fixes the template, page limit, paper size, review model, AI policy, deadlines and
  fees. Questions Q2–Q6, Q16 and Q21 depend on it.
- **Choices:** any IEEE conference whose scope fits applied AI and decision-support evaluation. Before choosing,
  check the official site, the IEEE conference record, the Xplore history and whether it is really indexed (the
  checklist is in `../conference_shortlist.md`).
- **Recorded:** no venue is selected.
- **Who:** all authors; A1 as corresponding author.
- **Blocks submission:** Yes.

**Q2. What is the venue's page limit, and do references count towards it?**
- **Context:** the draft is exactly 6 pages including references. Your stated preference is 6 pages; 7 is acceptable
  only if scientifically necessary or required by the venue.
- **Why it matters:** if the limit is below 6 pages, or references count and the limit is tight, material must move
  to supplementary material (see Q21). That needs your decision, because fonts and margins will not be shrunk.
- **Recorded:** a 6-page target (`../IMPLEMENTATION_PLAN.md` §10).
- **Who:** A1, after Q1.
- **Blocks submission:** Yes.

**Q3. Does the venue require A4 or US Letter paper?**
- **Context:** the draft compiles on US Letter (612 × 792 pt), IEEEtran's default.
- **Why it matters:** many IEEE conferences in India require A4. Switching to the `a4paper` class option changes the
  line breaks and can change the page count, so it must be re-checked.
- **Choices:** US Letter (current) or A4.
- **Who:** A1, after Q1.
- **Blocks submission:** Yes, if the venue specifies a size.

**Q4. Is the review double-blind?**
- **Context:** the draft shows all names, affiliations and e-mails, and the AI-use disclosure and the run identifiers
  could reveal the project.
- **Why it matters:** a double-blind venue would require an anonymised version: authors removed, self-identifying
  details neutralised, and possibly the repository URL withheld.
- **Choices:** single-blind (keep as is) or double-blind (prepare an anonymised copy).
- **Who:** A1, after Q1.
- **Blocks submission:** Yes, if double-blind.

**Q5. Does the venue require IEEE PDF eXpress or another compatibility check, and a copyright form?**
- **Context:** the PDF embeds all fonts. PDF eXpress has not been run, because it needs the venue's conference ID.
- **Why it matters:** IEEE Xplore-bound conferences usually require it for the camera-ready version.
- **Who:** A1, after acceptance or as the venue requires.
- **Blocks submission:** No for the initial submission; Yes for the camera-ready version.

**Q6. Are there other venue rules that affect the paper?**
- **Context:** examples are a keyword taxonomy, a limit on the number of authors, mandatory sections such as data or
  code availability, ethics or conflict-of-interest statements, and registration rules.
- **Why it matters:** any of these could require new short sections or statements, which must be written from the
  authors' facts, not invented.
- **Who:** A1, after Q1.
- **Blocks submission:** Depends on the venue.

## B. Authors, order, affiliations, e-mails and corresponding author

**Q7. Are the author names, their order and the 2 × 2 layout correct as printed?**
- **Context:** the order printed is A1 (top left), A2 (top right), A3 (bottom left), A4 (bottom right), exactly as
  instructed on 27 Nov 2026.
- **Why it matters:** the order cannot easily change after submission, and spellings must match each author's IEEE
  and ORCID records.
- **Recorded:** the order and names are "authoritative; do not reorder" in `../author_review_checklist.md` §C.
- **Needs:** each author confirms the spelling of their own name. Check particularly the initial in
  "P. Naga Bhargav Reddy" and whether a fuller form is preferred.
- **Who:** each author for their own name.
- **Blocks submission:** Yes, until each author has confirmed.

**Q8. Is the affiliation correct and complete for every author?**
- **Context:** all four blocks read "Department of Computer Science and Engineering, Vardhaman College of
  Engineering, Hyderabad, India", as instructed.
- **Why it matters:** an incorrect affiliation is an authorship-record error. It also matters if any author's role
  is staff rather than student, for example as the faculty mentor.
- **Recorded:** `../author_review_checklist.md` §C and `../../RESEARCH_STATE.md` §12.
- **Needs:** each author confirms. Some venues also want a state or postal code ("Hyderabad, Telangana, India").
- **Who:** each author.
- **Blocks submission:** Yes, until confirmed.

**Q9. Are the e-mail addresses correct, and are they the ones each author wants published?**
- **Context:** the printed addresses are A1 `syedasayeedafarhath@ieee.org`, A2 `siddharthreddy1908@gmail.com`, A3
  `nagabhargavreddy175@gmail.com` and A4 `anjali1820@vardhaman.org`.
- **Why it matters:** the addresses are published permanently, and the corresponding author's address receives
  reviewer correspondence. Some venues prefer institutional addresses.
- **Choices:** keep as printed, or substitute an institutional address for A2 and A3.
- **Recorded:** the addresses are taken from `../author_review_checklist.md` §C and your instruction of 27 Nov 2026.
- **Who:** each author.
- **Blocks submission:** Yes, until confirmed.

**Q10. Is A1 (Syeda Sayeeda Farhath) the corresponding author, and is the footnote form acceptable?**
- **Context:** A1 is marked with an asterisk and a first-page footnote, "Corresponding author." This uses the IEEE
  conference template's `\IEEEoverridecommandlockouts` + `\thanks` mechanism.
- **Why it matters:** some venues ask for the corresponding author to be marked differently, or only in the
  submission system.
- **Recorded:** A1 as corresponding author, confirmed 15 Nov 2026 (`../author_review_checklist.md` §D).
- **Needs:** confirm the presentation, or remove the footnote if the venue forbids `\thanks`.
- **Who:** A1.
- **Blocks submission:** No, unless the venue rules otherwise.

## C. Fourth authorship

**Q11. Has A4 (Baalne Anjali) completed, or will she complete, the substantive review and revision required for
authorship?**
- **Context:** the authors decided on 15 Nov 2026 that A4's authorship is conditional on substantively reviewing and
  revising the manuscript and approving the final version. The records note that professional academic guidance
  alone may not meet IEEE authorship criteria.
- **Why it matters:** IEEE requires every listed author to have made an intellectual contribution, taken part in
  drafting or critical revision, and approved the final version.
- **Choices:**
  - A4 reviews and revises the manuscript and remains fourth author;
  - or A4 is moved to the acknowledgments, with her consent.
- **Recorded:** `../author_review_checklist.md` §D and `../../RESEARCH_STATE.md` §12. No review by A4 is recorded yet.
- **Who:** A4, and all authors for the final decision.
- **Blocks submission:** Yes.

## D. Individual IEEE authorship eligibility and approval

**Q12. Does each author confirm that they meet IEEE authorship criteria and approve the final version?**
- **Context:** each author must confirm an intellectual contribution, drafting or critical revision, approval of the
  final version (including references), and acceptance of responsibility. The roles recorded so far are:
  - A1: research direction, coordination and the pilot and P7 reviews;
  - A2: implementation-side work and review and acceptance of S1;
  - A3: literature survey;
  - A4: guidance.

  No CRediT contribution statement has been written; none will be invented.
- **Why it matters:** this is an IEEE requirement and a legal attestation at submission.
- **Recorded:** the roles and the open confirmations in `../author_review_checklist.md` §D. A2's review of the S1
  code was confirmed on 27 Nov 2026.
- **Needs:** a written confirmation from each author. If the venue requires a contribution statement, each author
  provides their own (Q6).
- **Who:** A1, A2, A3 and A4, each individually.
- **Blocks submission:** Yes.

## E. AI-use disclosure

**Q13. Do all authors approve the AI-use disclosure in the Acknowledgment section, and does it meet the venue's
policy?**
- **Context:** the disclosure names Claude (Anthropic, used through Claude Code) and lists its extensive use:
  - repository analysis;
  - support for planning and evaluation design;
  - writing the S1, benchmark, evaluation, statistics and run-control code and tests;
  - executing the authorised stages;
  - verifying literature metadata;
  - drafting the manuscript.

  It is **not** limited to language editing, and it states that the authors made the decisions and are responsible
  for all content. The factual basis is in `ai_use_disclosure.md`.
- **Why it matters:**
  - IEEE requires disclosure of AI-generated content, naming the system and the sections and extent;
  - some venues require a model or version, or a dedicated section;
  - an inaccurate disclosure is a publication-ethics issue.
- **Choices:** approve as written; edit for accuracy (only towards a more accurate account); or add a version or
  section if the venue requires it.
- **Recorded:** the disclosure must be accurate and must not understate the assistance (`../IMPLEMENTATION_PLAN.md`
  §10). The wording is not yet agreed (`../author_review_checklist.md` §E).
- **Who:** all authors.
- **Blocks submission:** Yes.

## F. Funding

**Q14. Does the venue require an explicit "no funding" statement?**
- **Context:** the draft contains no funding statement.
- **Why it matters:** some venues require an explicit declaration; others treat absence as "none".
- **Choices:** keep no statement, or add "This work received no external funding."
- **Recorded:** external funding is **none**, with no funding acknowledgement, confirmed 15 Nov 2026
  (`../author_review_checklist.md` §D).
- **Suggested default:** no statement, unless the venue requires one.
- **Who:** A1.
- **Blocks submission:** Only if the venue requires the statement.

## G. References that could not be machine-verified

**Q15. Can an author verify Holm (1979) and ISO 3166-1 by hand?**
- **Context:**
  - `holm1979` (S. Holm, "A Simple Sequentially Rejective Multiple Test Procedure," *Scand. J. Statist.* 6(2):65–70,
    1979; JSTOR 4615733) has no Crossref DOI, and JSTOR blocked automated access.
  - `iso3166` (ISO 3166-1, iso.org) returned HTTP 403 to automated requests; the study itself used ISO 3166-1 through
    the pycountry 26.2.16 package.
- **Why it matters:** both are cited in the methodology. They remain marked **AUTHOR-CHECK** in
  `bibliography_verification.md` and will not be marked verified without a manual check.
- **Needs:** open both sources in a browser, confirm every bibliographic field, and record the result in
  `bibliography_verification.md`. For ISO, decide whether to cite the standard's edition (e.g. ISO 3166-1:2020) or
  the country-codes page.
- **Who:** A3.
- **Blocks submission:** Yes.

## H. Content-level review of the cited literature

**Q16. Has every citing sentence been checked against the full text of the cited work?**
- **Context:** the metadata of 31 entries was verified (Crossref, publisher pages, files). **Their content has not
  been reviewed:** the drafting session did not read the full texts. The statements needing particular care are:
  - Related Work: abstention in [chow1970, elyaniv2010, geifman2017, kamath2020, xin2021] is described as "typically
    derived from model confidence";
  - [koch2025] and [wube2026]: only their titles were available, so the paper says no more than the titles;
  - [ding2015], [kim2020date] and [mikuriya2020], cited for their topics;
  - [finkel2006], [sculley2015], [breck2017], [ribeiro2020] and [kapoor2023], cited for general points about
    pipelines, testing and leakage.
- **Why it matters:** a citation that does not support its sentence is a scientific-integrity problem, and reviewers
  check this.
- **Choices:** confirm as written; reword a sentence; or replace or remove a citation. Any new reference must itself
  be verified.
- **Who:** A3 (literature survey), with A1.
- **Blocks submission:** Yes.

**Q17. Should Related Work include more recent work, for example 2021–2026 HS-classification or customs-AI papers
read in full?**
- **Context:** the current set is deliberately limited to verified sources. Recent HS work is represented only by
  koch2025 and wube2026, at title level.
- **Why it matters:** reviewers may expect wider coverage of recent applied work.
- **Choices:** keep the set as is, or add papers that A3 has read and verified.
- **Who:** A3.
- **Blocks submission:** No.

## I. Scientific interpretations, numbers, tables, keywords and title

**Q18. Do all authors approve the main interpretations?**
- **Context:** the interpretations are:
  - S1's held-out country safety comes from abstention, not from identification;
  - S1's tax-behaviour result is achieved by refusal, including 137 over-refusals where tax data existed;
  - S0 is not more accurate than B on products (−0.022, Holm p = 1);
  - product errors did not change costs *because* the prototype's tax table is keyed by country only, while country
    errors propagated.
- **Why it matters:** these are the paper's claims, and the authors are accountable for them.
- **Recorded:** the evidence is in `claim_evidence_audit.md` (rows C9–C21) and `../test_results_report.md`.
- **Who:** all authors.
- **Blocks submission:** Yes.

**Q19. Have the numbers and tables been checked independently?**
- **Context:**
  - every number traces to a committed file (`claim_evidence_audit.md`);
  - the tables and Fig. 1 are generated by `make_tables.py` from the committed TEST run
    `20261127T104925Z-0f293784`;
  - Fig. 1 was redrawn from the committed summary CSVs, because the frozen run's own figures have a cosmetic title
    overlap; the data are identical.
- **Why it matters:** an independent author check catches transcription or interpretation errors before reviewers do.
- **Needs:** at least one author reruns `python make_tables.py` (or compares the tables with the CSVs) and spot-checks
  the claims in `claim_evidence_audit.md`.
- **Who:** A2 and at least one other author.
- **Blocks submission:** Yes.

**Q20. Do the system descriptions (Section III) match the code?**
- **Context:** the paper describes B, S0 and S1 as fixed sequential Python pipelines with no LLM and no autonomous
  agents, and states the stage order, matching rules, defaults (5 % duty, 10 % VAT, exchange rate 1.0 in S0) and S1's
  evidence tiers.
- **Why it matters:** describing the implementation accurately is a stated project rule.
- **Who:** A2.
- **Blocks submission:** Yes.

**Q21. Are the keywords and the title final?**
- **Context:**
  - the title is the approved working title (`../IMPLEMENTATION_PLAN.md` §10), which may be refined only now that
    results exist, without changing the research question;
  - the keywords are: selective prediction, abstention, silent errors, customs pre-assessment, Harmonized System,
    entity resolution, error propagation.
- **Why it matters:** the venue may require keywords from a taxonomy, and the title is fixed at submission.
- **Choices:** keep, or revise; a revised title must still describe the same study.
- **Who:** all authors.
- **Blocks submission:** Yes, until confirmed.

## J. Supplementary material

**Q22. Does the venue require or allow supplementary material, and should any be provided?**
- **Context:** the full DEV and TEST reports, the run records, the per-item outputs and the code are in the
  repository. The paper does not state public availability of the code or data.
- **Why it matters:**
  - some venues require, or reward, a data or code availability statement or an artefact;
  - supplementary material can hold content cut for page limits, such as full per-category tables or DEV latency;
  - publishing the repository needs the authors' consent and checks for personal data. The repository contains
    author e-mails and personal review notes.
- **Choices:** no supplementary material; a supplementary PDF; or a public artefact (repository snapshot or archive)
  with an availability statement.
- **Who:** all authors; A1 to check the venue's rules.
- **Blocks submission:** Depends on the venue.

## K. Other decisions

**Q23. Should the paper mention that the synthetic data and prototype will not be released, or will be?**
- **Context:** this links to Q22. The draft states that the data are synthetic and that the HS source is an
  unofficial mirror, but says nothing about release.
- **Who:** all authors.
- **Blocks submission:** No, unless the venue requires an availability statement.

**Q24. Are the presentation choices acceptable?**
- **Context:** the choices are:
  - one sentence on DEV latency (indicative only);
  - the exploratory ladder table (Table VI) and the malformed-input results kept separate from the confirmatory
    results;
  - a sentence in §I explaining that the prototype's "agent" stage names do not denote agents.
- **Choices:** keep, or move to supplementary material (Q22).
- **Who:** all authors.
- **Blocks submission:** No.

---

## Not to be changed without a new authorisation
The frozen code, data, exclusions, configuration, manifest, DEV outputs and the TEST run
`20261127T104925Z-0f293784` must not change. Any rerun would require `--rerun-reason` and a separate authorisation,
and would have to be reported.

## Summary
| Blocks submission | Questions |
|---|---|
| Yes | Q1, Q2, Q3*, Q4*, Q7, Q8, Q9, Q11, Q12, Q13, Q15, Q16, Q18, Q19, Q20, Q21 |
| Depends on the venue | Q6, Q14, Q22, Q23 |
| No (or camera-ready only) | Q5, Q10, Q17, Q24 |

\* if the venue specifies a paper size or double-blind review.
