# Manuscript change log

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
