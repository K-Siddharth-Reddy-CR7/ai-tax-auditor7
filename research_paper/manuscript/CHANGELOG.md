# Manuscript change log

## Revision 3 (27 Nov 2026): presentation revision, table audit, Overleaf project
- **Structure:**
  - Bold run-in paragraph headings were replaced by IEEE lettered subsections (III-A/B, IV-A/B/C, V-A to V-D) and
    plain prose. Related Work and Threats to Validity are now prose paragraphs.
  - Section VI was renamed "Threats to Validity"; Section VII remains "Conclusion".
  - No methodological information was removed.
- **Author block:** the corresponding-author asterisk and the first-page footnote were removed. The 2 × 2 layout,
  order, names, affiliations and e-mails are unchanged. A1's corresponding-author status is unchanged in the project
  records (questionnaire Q10).
- **Abstract:** the country-identification sentence was replaced by the authors' corrected sentence (no system
  *reliably* identified held-out forms; S0 identified three J5 items and made 12 silent identification errors). It was
  verified against the TEST outputs. The conclusion was aligned with it.
- **Table V (corrected presentation, no value changed):**
  - It is rebuilt as mutually exclusive propagation classes with flagged and silent cases separated and a total row
    (359 and 769 for every system).
  - The former "Fabricated HS code" row (S0: 120) was an overlapping attribute. It is now labelled as an overlap and
    footnoted with its breakdown: 83 should-decline-silent, 33 wrong-product-silent and 4 no-error, where S0's
    fallback 8471.30 equals the true code.
  - The product landed-cost row (all zero) is always shown.
- **Wording:** "S0 fabricates an HS code for 120 items" became "outputs its hard-coded fallback code 8471.30 for 120
  items (four coincide with the true code)".
- **Fig. 1:** regenerated from the committed TEST outcome data, and every bar was verified. The caption now gives
  the denominators.
- **AI-use disclosure:** the editorial placeholder was removed and the substance kept. Approval by all four authors
  and a venue-policy check remain open (Q13).
- **Audit:** the new `audit_tables.py` independently recomputes Tables I–VI, Fig. 1 and the abstract claim from the
  per-item TEST outputs and benchmark files. All 145 checks passed (`table_figure_audit.md`).
- **Overleaf:** added `LEXITAX_IEEE_Overleaf/` and `LEXITAX_IEEE_Overleaf.zip`. They were tested by compiling from a
  fresh extraction: the project compiled independently to an identical 6-page PDF.
- **Unchanged:**
  - title, research question, methods, all DEV/TEST results, statistics, references and conclusions (apart from the
    aligned country sentence);
  - IEEEtran class options and dimensions;
  - 6 pages including references.

## Revision 2 (27 Nov 2026): targeted author-block correction
- **Author block** (`main.tex`): replaced the single combined author block with four IEEE author blocks in two
  columns and two rows.
  - Top left, A1: Syeda Sayeeda Farhath. Top right, A2: Siddharth Karanam.
  - Bottom left, A3: P. Naga Bhargav Reddy. Bottom right, A4: Baalne Anjali.
  - Each block has the department, college, "Hyderabad, India" and the author's e-mail, exactly as instructed.
  - The new row uses the `\linebreakand` construct, a redefinition of IEEEtran's author-alignment environment, with
    no manual spacing.
- **Corresponding author:** A1 is marked with an asterisk and a first-page footnote ("Corresponding author."). This
  uses `\IEEEoverridecommandlockouts` and `\thanks`, as in the official IEEE conference template.
- **Unchanged:**
  - title, abstract, body text, tables, figure, references, AI-use disclosure and all results;
  - the IEEEtran class, font size, margins and column dimensions;
  - page count: 6 pages including references, as before.
- `author_review_items.md` was rewritten as a numbered author questionnaire (Q1–Q24). Each question gives the
  context, why it matters, the choices, what is already recorded, who must answer, and whether it blocks submission.
- `bibliography_verification.md` and `README.md` now say "metadata-verified" explicitly (no content-level review yet).

## Revision 1 (27 Nov 2026, commit 6d6df7c): first complete draft
- `main.tex` and `main.pdf` (6 pages), `references.bib` (33 entries), `bibliography_verification.md`,
  `claim_evidence_audit.md`, `ai_use_disclosure.md`, `author_review_items.md` and `make_tables.py` with the generated
  `tables/`, `figures/` and `generated_values.json`.
