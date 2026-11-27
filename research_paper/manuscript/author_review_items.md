# Outstanding items requiring author input (manuscript draft of 27 Nov 2026)

**Status: DRAFT FOR AUTHOR REVIEW. Not submission-ready. Nothing has been submitted.** Every author must read,
verify, revise and approve the manuscript.

## A. Blocking before submission
| # | Item | Who |
|---|---|---|
| A1 | **Select the target venue** and verify its template, page limit (whether references count), paper size (the draft is US Letter; many venues require A4), anonymisation rules (the draft is *not* anonymised) and AI policy. The draft follows the generic IEEEtran conference template and is exactly 6 pages including references | All; see `../conference_shortlist.md` |
| A2 | Confirm the author block: names and order, the single shared affiliation, the e-mail addresses (taken from `../author_review_checklist.md` §C) and Author 1 as corresponding author | All |
| A3 | **Author 4 (Baalne Anjali):** authorship is conditional on substantive review and revision of the manuscript and final approval (`../author_review_checklist.md` §D). Confirm, or move her to the acknowledgments | Author 4, all |
| A4 | Per-author IEEE authorship confirmation (intellectual contribution, drafting or critical revision, approval of the final version, accepting responsibility) | Each author |
| A5 | Approve or correct the **AI-use disclosure** (`ai_use_disclosure.md`), checked against the venue's policy | All |
| A6 | Funding: none is recorded (`../author_review_checklist.md` §D). The draft has no funding statement. Add one if the venue requires an explicit "no funding" statement | Author 1 |

## B. Scientific verification
| # | Item | Who |
|---|---|---|
| R1 | **Read every cited work** and confirm that each citing sentence is accurate. Only metadata was verified (`bibliography_verification.md`); full texts were not read. Check in particular the Related Work statements on [chow1970, elyaniv2010, geifman2017, kamath2020, xin2021] ("typically derive abstention from model confidence"), [koch2025, wube2026] (title-level only) and [mikuriya2020] | Author 3 |
| R2 | Verify by hand the two entries that could not be machine-checked: `holm1979` (Scand. J. Statist. 6(2):65–70, JSTOR 4615733) and `iso3166` (iso.org page) | Author 3 |
| R3 | Check the system descriptions (§III) against `backend/server.py` and `backend/lexitax_v2/` | Author 2 |
| R4 | Check each number against `claim_evidence_audit.md` (or rerun `python make_tables.py` and compare) | Author 2 and one other author |
| R5 | Confirm the interpretations: S1's country and tax safety "comes from abstention / refusal"; "S0 is not more accurate than B"; product errors do not change costs *because* the tax table is keyed by country. Also the limitation statements in §VI | All |
| R6 | Decide whether the keywords suit the venue | All |
| R7 | The title is the approved working title. Confirm it, or propose a more precise one now that results exist (the research question must not change) | All |

## C. Presentation choices the authors may revise
- **Figure 1** was regenerated from the committed TEST summary CSVs by `make_tables.py`. The frozen run's own figures
  have a cosmetic title overlap (`../test_results_report.md` §1). No data differ.
- **DEV latency** appears in one sentence only, as indicative DEV results; the full numbers are in
  `../dev_results_report.md`.
- **The exploratory ladder table** (Table VI) and the malformed-input results are kept separate from the confirmatory
  results. They could move to an appendix or supplementary material if the venue's page limit requires it.
- **Wording** about the prototype's own terminology ("agent" stage names) is in §I. Keep or shorten.

## D. Not to be changed without a new authorisation
The frozen code, data, exclusions, configuration, manifest, DEV outputs and the TEST run
`20261127T104925Z-0f293784` must not change. Any rerun requires `--rerun-reason` and separate authorisation, and would
have to be reported.
