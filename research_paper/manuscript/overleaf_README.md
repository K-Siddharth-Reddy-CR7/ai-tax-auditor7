# LEXITAX AUDIT: IEEE conference manuscript (Overleaf project)

**Status: DRAFT FOR AUTHOR REVIEW. Not submitted. Do not submit until every author has proofread and approved it.**

Title: *Silent Errors versus Safe Abstention in Staged Customs Pre-Assessment: An Empirical Study of Product and
Jurisdiction Resolution*

Authors, in fixed order: Syeda Sayeeda Farhath, Siddharth Karanam, P. Naga Bhargav Reddy, Baalne Anjali.

## Contents

| Path | Purpose |
|---|---|
| `main.tex` | Main document (IEEEtran, `conference` option) |
| `references.bib` | Bibliography (33 entries, all cited), processed with BibTeX and `IEEEtran.bst` |
| `tables/*.tex` | The six tables, included with `\input`. They are generated from the committed experiment results; do not edit numbers by hand |
| `figures/test_outcomes.pdf` | Fig. 1, generated from the committed TEST results |
| `IEEEtran.cls`, `IEEEtran.bst` | Unmodified IEEE template files, v1.8b (2015/08/26), included so that the project is self-contained |
| `main.pdf` | The compiled draft (6 pages, US Letter), for comparison |

## Upload to Overleaf
1. In Overleaf choose **New Project → Upload Project** and select `LEXITAX_IEEE_Overleaf.zip`.
2. Open **Menu** and set **Compiler** to **pdfLaTeX** and **Main document** to `main.tex`.
3. Click **Recompile**. Overleaf runs pdfLaTeX and BibTeX automatically; there is no separate bibliography step.

## Compile locally (same workflow)
Run this in the project folder. It needs TeX Live with `latexmk`, `pdflatex` and `bibtex`:

```bash
latexmk -pdf main.tex
```

Packages used are all standard in TeX Live and Overleaf: `fontenc`, `cite`, `amsmath`, `graphicx`, `booktabs`, `url`
and `hyperref`.

## Licence of the template files
`IEEEtran.cls` and `IEEEtran.bst` are by Michael Shell and contributors and are distributed under the LaTeX Project
Public License (LPPL) 1.3. They are included unmodified. The official IEEE conference template can also be
obtained from the IEEE Author Center ("IEEE Article Templates") or from CTAN (`ieeetran`). If the selected conference
supplies its own template, use that version instead.

## Notes for the authors
- The target conference has not been selected. Its page limit, paper size (this draft is US Letter; use the
  `a4paper` class option if A4 is required), review model and AI policy must be checked before submission.
- All open decisions are listed in the project repository's author questionnaire
  (`research_paper/manuscript/author_review_items.md`), which is not part of this upload.
