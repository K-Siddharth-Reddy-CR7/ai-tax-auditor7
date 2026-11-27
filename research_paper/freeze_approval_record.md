# LEXITAX AUDIT — Experimental Freeze Approval Record

Permanent record of the joint author approval of the experimental freeze package. This file records approvals
only. **The freeze itself (`run_all.py --stage freeze`, which writes `data/generated/MANIFEST.json`) has NOT been
executed at the time this record was committed.** No tuning, latency measurement, DEV evaluation or TEST
evaluation had been performed.

## 1. Approved freeze package

| Item | Approved value |
|---|---|
| Repository | `https://github.com/K-Siddharth-Reddy-CR7/ai-tax-auditor7` |
| Branch | `research/option-a-evaluation` |
| Approved commit | `0e5a831c99dd62f098f6c1258fd2c0fe5453eb98` |
| Code identity (38 files, `lexeval/run_control.py::CODE_IDENTITY_PATTERNS`) | `1930a0b2b99eb6587879b9b330af93a7eb3d2a3df447dcc1e1c09b22fd44efb6` |

The seven approved file hashes (SHA-256), as they will appear in `MANIFEST.json`:

| # | Manifest field | File (under `research_paper/experiments/`) | SHA-256 |
|---|---|---|---|
| 1 | `files.product_benchmark.csv` | `data/generated/product_benchmark.csv` | `a6a87fc3f7057a74eebd9d5b7809809820b892e4ac3b791fe1f4dc64c5935160` |
| 2 | `files.country_benchmark.csv` | `data/generated/country_benchmark.csv` | `1bf3f48940c27b4ba7fad332bc8e0bbc367df1381a251e6345a3a6609444c929` |
| 3 | `files.malformed_inputs.csv` | `data/generated/malformed_inputs.csv` | `bb3af78811f382e8f1bcab7d622cfbe0737177a7a4644e8724b0258ef19655df` |
| 4 | `files.excluded_items.csv` | `data/generated/excluded_items.csv` | `fcdc6789fbb455b78c3f0f5229ba9eacdde111b42dadf61f7283e6b2717f44d1` |
| 5 | `config_sha256` | `config.json` | `ba8b5ef73626f68f1b18aa33a25df484c4ed130583ff7489295b9e5162640373` |
| 6 | `review_treatments_sha256` | `pilot/authorised_review_treatments_v1.csv` | `cc5f593f172964ff352aa434d682db990d8713e52e7a92dd77a2b99ba38f15ce` |
| 7 | `evaluation_exclusions_sha256` | `evaluation_exclusions_v1.json` | `2ecacabef8cffc751fcd894437693bbd2681157a5b8c055504e5fb4252f4e203` |

Benchmark sizes at the approved commit: product 805 rows (DEV 270 / TEST 535); country 2,122 (DEV 655 / TEST
1,467); malformed inputs 18; `excluded_items.csv` 4 rows (the four P7 benchmark exclusions). The eight pilot TEST
exclusions are listed in `evaluation_exclusions_v1.json`. The design that was approved is summarised in the freeze
approval package (sections B–C) and specified in `RESEARCH_STATE.md` §§2–4, 9–11 and `config.json`.

## 2. Approvals

Both approvals were given on **27 November 2026**, independently, and were conveyed to the research session by the
user on that date. The confirmations below are recorded as conveyed; no signed copy is stored in this repository.

### 2.1 Author 1 — Syeda Sayeeda Farhath (Corresponding Author)
Date of approval: **27 November 2026**

The corresponding author independently confirmed:
- review and approval of the complete freeze package;
- all seven recorded dataset/configuration/review/exclusion/code hashes;
- the four P7 benchmark exclusions;
- the eight pilot TEST exclusions;
- strict DEV-only tuning;
- the evaluation and statistical design;
- retention and disclosure of the unofficial HS 2022 mirror;
- understanding that changes to frozen files invalidate the TEST evaluation.

### 2.2 Author 2 — Siddharth Karanam
Date of approval: **27 November 2026**

Author 2 independently confirmed:
- review and approval of the same freeze package and commit;
- the same code identity and hashes;
- review of `backend/lexitax_v2/` and acceptance of S1;
- the four P7 benchmark exclusions;
- the eight pilot TEST exclusions;
- strict DEV-only tuning;
- the evaluation and statistical design;
- retention and disclosure of the unofficial HS 2022 mirror;
- understanding that changes to frozen files invalidate the TEST evaluation.

## 3. Notes by the preparer of this record (not part of the authors' approvals)

1. **Commit recorded by the freeze.** This record is committed on top of the approved commit, so the freeze will be
   executed at a later commit than `0e5a831` and `MANIFEST.json` will record that later commit as
   `code_identity.git_commit`. The later commit changes documentation only (this file and
   `research_paper/author_review_checklist.md`), none of which is a code-identity path. For the freeze to correspond
   to this approval, the written manifest must record:
   - `code_identity.sha256` = `1930a0b2b99eb6587879b9b330af93a7eb3d2a3df447dcc1e1c09b22fd44efb6`;
   - the seven file hashes in §1, unchanged;
   - a `git_commit` that descends from `0e5a831c99dd62f098f6c1258fd2c0fe5453eb98` with
     `git diff --name-only 0e5a831 <git_commit>` touching no code-identity path.
2. **Freeze command (not yet run).** From `research_paper/experiments` with the pinned environment:
   `python run_all.py --stage freeze --approved-by "Syeda Sayeeda Farhath (Corresponding Author) and Siddharth
   Karanam (Author 2), joint approval of freeze package at commit 0e5a831 (see research_paper/freeze_approval_record.md)"`.
   The `approved_by` field is free text and is not itself verified; this record is the evidence behind it.
3. **Pinned wording left unchanged.** `evaluation_exclusions_v1.json` records `"authorised_by": "User (research
   session instruction); author confirmation to be recorded in author_review_checklist.md"`, and
   `pilot/authorised_review_treatments_v1.csv` records the authoriser as "Authors (decision conveyed by the user in
   the research session)". Both files are pinned and are deliberately not edited; the author confirmations are
   recorded here and in `author_review_checklist.md`.
4. **HS source.** The HS 2022 descriptions come from the unofficial mirror `datasets/harmonized-system` (commit
   `b1be3f2`, ODC-PDDL-1.0, UN Comtrade-derived, abridged descriptions, not WCO legal text; file SHA-256
   `e77ee9e1cfd15a42d1fadeb2c0618d10f6b9ed9aec0e5d66826dc7ef9d3126a5`). The paper must disclose this and must not
   claim official or legal classification validity.
5. **Remote `main`.** PR #1 merged `0e5a831` into `main` (merge commit `0383ff7`, tree identical to `0e5a831`). The
   research branch contains no merge commit. `main` must not be merged back into the research branch before the
   TEST evaluation.
