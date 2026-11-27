# Manuscript workspace (IEEE conference paper)

**Status (26 Nov 2026): WORKSPACE AND OUTLINE ONLY.**
- No manuscript text, reference, table, figure or result exists yet.
- Drafting (Stage 1) has not been authorised.
- Governing plan: `IMPLEMENTATION_PLAN.md` §10 (deliverable and rules) and §8 (project sequence).

## Planned contents
| File | Content | Stage | Status |
|---|---|---|---|
| `outline.md` | Section plan with evidence sources and placeholders | — | Present |
| `main.tex` | Manuscript in the selected IEEE conference template (template not yet selected or verified) | 1 → 2 | Not started |
| `references.bib` | Verified references only (IEEE style) | 1 | Not started |
| `literature_evidence_table.md` | Title, authors, year, venue, DOI or verified source, contribution, relevance, how cited, verification status | 1 | Not started; candidate leads in `../literature_review.md` are unverified |
| `traceability.md` | Every numerical claim → result file, dataset record or calculation | 2 | Not started |
| `author_verification_checklist.md` | Items each author must check (methods vs code, references, statistics, claims) | 1 → 2 | Not started; see also `../author_review_checklist.md` |
| `open_questions.md` | Unresolved methodological questions | 1 → 2 | Not started |
| `ai_use_disclosure.md` | Disclosure draft, matched to the venue's current AI policy | 1 → 2 | Not started |
| `figures/`, `tables/` | Generated from `../experiments/results/` only | 2 | Not started |
| `main.pdf` | Compiled and page-checked | 2 | Not started |

## Rules (summary; full list in `IMPLEMENTATION_PLAN.md` §10 and `RESEARCH_STATE.md` §0)
- **References:** real and verified only.
- **Numbers:** every number traces to a file. No result or comparative claim before the authorised TEST evaluation.
- **Implementation as it is:**
  - B, S0 and S1 are fixed sequential Python functions with no LLM;
  - policy lookup is a prototype TF-IDF retriever, not generative RAG;
  - the data are synthetic or prototype;
  - the HS source is an unofficial mirror;
  - no legal classification or compliance claim.
- **Authors:** order as fixed; no invented contributions, approvals or funding.
- **AI use:** disclosed accurately.
