# Manuscript workspace (IEEE conference paper)

**Status (27 Nov 2026): COMPLETE DRAFT FOR AUTHOR REVIEW. Not submission-ready and not submitted.**
- Written after the freeze, the DEV stage and the single TEST run `20261127T104925Z-0f293784`.
- Results come only from the committed result files.
- The authors must read, verify, revise and approve the paper (`author_review_items.md`).

## Files
| File | Content |
|---|---|
| `main.tex` | Manuscript (generic IEEEtran conference template; venue not yet selected) |
| `main.pdf` | Compiled rendering: 6 pages including references, US Letter |
| `references.bib` | Bibliography: 33 entries, all cited |
| `bibliography_verification.md` | DOI/URL and verification status of every entry (31 verified, 2 need an author check) |
| `claim_evidence_audit.md` | Each major claim mapped to the exact result file, row or code |
| `ai_use_disclosure.md` | AI-use disclosure draft and its factual basis |
| `author_review_items.md` | Everything that needs author input before submission |
| `make_tables.py` | Generates `tables/*.tex`, `figures/test_outcomes.pdf` and `generated_values.json` from the committed results (read-only) |
| `tables/`, `figures/`, `generated_values.json` | Generated; do not edit by hand |
| `outline.md` | Original section plan (26 Nov 2026), kept for history |

## Rebuild
Run from this folder, with Python 3.13 and the pinned `../experiments/requirements.txt` environment (matplotlib), plus TeX Live with IEEEtran:

```bash
python make_tables.py
```

```bash
latexmk -pdf main.tex
```

## Rules
- **References:** real and verified only.
- **Numbers:** every number traces to a committed file.
- **Systems:** described as they are. They are fixed sequential Python pipelines with no LLM; policy lookup is a
  prototype TF-IDF retriever.
- **Data:** synthetic and prototype; the HS source is an unofficial mirror. The paper makes no legal or compliance
  claim.
- **Authors:** the order is fixed. No invented contributions, approvals or funding.
- **AI use:** disclosed accurately.
