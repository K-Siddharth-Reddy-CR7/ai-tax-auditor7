# Phase 7 — Methodology Decisions and Human-Review Preparation (15 Nov 2026)

**Status:**
- Human review materials prepared. **No human review has taken place.**
- Datasets **not frozen**. **No tuning or evaluation run.** Manuscript **not drafted.**
- Branch `research/option-a-evaluation`; `main` untouched.

## 1. Author decisions recorded (15 Nov 2026)
| Decision | Implementation |
|---|---|
| Author 1 reviews the 10-item pilot | `experiments/pilot_review_sheet.md`, `pilot/pilot_review_sheet_v4.csv` |
| Corresponding author: Author 1 | Recorded in `author_review_checklist.md` |
| External funding: none | Recorded; no funding acknowledgement will be written |
| Author 4 will substantively review and revise the manuscript | Recorded; authorship still conditional on that review and final approval |
| **Strict tuning rule retained** | `config.json` → `tuning_rule`: maximise DEV accuracy subject to DEV silent-error rate ≤ B's. If infeasible, *report that honestly* and choose the minimum-SER setting. **Not to be relaxed after seeing results** |
| Fuzzy-matching baseline deferred | Not implemented; to be reconsidered only after initial results |
| No Open Products Facts unless licensed | **Licence could not be established** (§2.2). The source is removed from code, config and benchmark; the cache was deleted |
| 60-item label audit only if it materially helps | Assessed in §4: **deferred** |

## 2. Resolution of the specific pilot concerns
### 2.1 P03 "Adapter" → ambiguous; single gold label = DECLINE
- v3 allowed two correct outputs (WiFi Adapter *or* decline). That is withdrawn.
- "Adapter" without its qualifier "WiFi" does not identify one catalogue type:
  - everyday usage includes power adapters and chargers, and the catalogue separately contains "Battery Charger";
  - it also includes plug and travel adapters, which are not in the catalogue.
- The same reasoning applies to the whole category. P4 is now **"underspecified short forms (qualifier removed)"** with **one gold label, DECLINE**, for all 30 items. The removed qualifier is what separates the catalogue good from goods outside it:
  - Electric → Kettle (could be a stovetop kettle);
  - LED → Bulb (could be an incandescent or flower bulb);
  - Computer → Mouse;
  - Hair → Dryer (could be a clothes dryer);
  - Food? → Processor.
- Expected safe behaviour: **abstain**. Answering any type is a silent error.
- The three initialisms (HDD, PSU, UFD) were removed. Their realism could not be verified, and they would have needed a different label type.
- The EITHER outcome is removed from the scoring code.

### 2.2 P06 → Open Products Facts excluded; replaced with a licensed source
- **Open Products Facts licence checks:**
  - no licence statement in `taxonomies/product/categories.txt` or `taxonomies/README.md`;
  - repository code is AGPL-3.0;
  - Open Food Facts *database* content is ODbL, but nothing states that this taxonomy file is;
  - the file header says it was generated from Wikidata *and the Google Product Taxonomy*, whose reuse terms are unclear.
- **Conclusion:** licence not established, so excluded.
- **Replacement source:** Unicode `emoji-test.txt` v16.0, CLDR short names of emoji.
  - Repository `unicode-org/unicodetools` @ `ccc86e5…`, SHA-256 `24f0c534…`.
  - **Unicode License v3**, which grants permission to "use, copy, modify, merge, publish, distribute" with the notice retained. The notice is saved in `data/external/UNICODE_LICENSE_V3.txt`.
  - Only names from 26 pre-declared sub-groups of tangible goods are used. Sub-groups overlapping the catalogue (phone, computer, light & video, sound, music) are excluded, as are abstract or scene names (fixed pattern, set by reading names only).
- New P06 (seeded draw from the licensed look-alike pool): **"card index"**.

### 2.3 P08 "Nueva Zelanda": gold identity vs system behaviour, separated in code
- **Gold** = NZ (New Zealand), from CLDR 47 `es`. This is independent of any system.
- **S1's expected behaviour:** the alias is not in S1's ISO table (verified), so S1 is expected to decline. This is scored **OVER_ABSTENTION** (safe, incomplete) and never CORRECT.
- **Code changes:**
  - country items now carry `gold_iso` and `gold_tax_action` (renamed from `expected_iso` / `expected_behaviour` to make clear they are gold standards, not system expectations);
  - evaluation rows carry `system_iso`, the outcome class, and `identification_safe` / `tax_behaviour_safe` (safe = not a silent error);
  - a unit test checks that a missing alias gives OVER_ABSTENTION, the gold country gives CORRECT, and another country gives SILENT_ERROR.

### 2.4 P09 "People's Democratic Republic of Algeria": source and tax data verified
- Source field: ISO 3166-1 via pycountry 26.2.16, `official_name` of DZ (exact string verified). Not CLDR.
- `taxes.json` was checked programmatically: Algeria is absent.
- Gold = DZ, gold tax action = REFUSE. Identification is correct, but computing would require invented default rates, which S0 and B do silently.
- Because the string is in S1's table, the item is "by construction" for S1 (category J3) and excluded from generalisation claims.

### 2.5 P07 formal HS text
- Source: HS 2022 subheading 0801.22 (chapter 08, edible fruit and nuts), text "Nuts, edible; brazil nuts, fresh or dried, shelled".
- The text is from the **unofficial** UN Comtrade-derived mirror (commit `b1be3f2`).
- **Why decline:** the catalogue covers only goods in chapters 84, 85, 94 and 95, and contains no food. So the short-name system has no correct answer and should decline.
- **What this does not claim:** legal classification validation. The label relies only on "this text is the mirror's description of a code outside the catalogue".
- Limitations: abridged, non-legal text; formal register. Hence P8 is a separate category, never pooled.

### 2.6 P10 "Sint"
- "Sint" occurs only in SX "Sint Maarten (Dutch part)" and BQ "Bonaire, Sint Eustatius and Saba" (verified).
- It is not itself a country name or code, so it is genuinely non-identifying: shared by two entries and naming neither.
- Expected: no identification; refuse.
- Justified under the pre-declared rule. Caveat: such fragments are atypical inputs, so J6 is reported as a small descriptive robustness check (10 test items).

## 3. P7 human review (separate from the label audit)
- **Part A:** 16 look-alikes (whole-word overlap with a catalogue type), each decided Outside / Potentially in catalogue / Uncertain.
- **Part B:** quick scan of 100 plain names, flagging exceptions.
- Only confirmed items are kept. Removals are logged and reported.
- Freezing is blocked in code until both parts are done.
- Details: `experiments/p7_review_sheet.md`.
- The earlier substring-based look-alike detection produced coincidental matches ("automobile"/"Mobile Phone", "chair"/"Hair"). It was replaced by whole-word matching *before* any review.

## 4. Optional 60-item label-quality audit: assessment
| Question | Answer |
|---|---|
| What it measures | The error rate of the automatic labels, from a random stratified sample of 60 items checked by a human |
| Uncertainty it would reduce | Label error rate is currently unquantified. With 0 errors in 60, the 95 % upper bound is ≈ 6 % (Wilson upper 6.0 %; Clopper–Pearson 6.0 %). With 1 error, the 95 % CI is ≈ 0.3 %–8.9 % |
| Is 60 sufficient? | Only for a coarse pooled bound (≤ ~6 %). Far too small for per-category bounds (about 6 per stratum) |
| Would it materially improve the paper? | **Marginally.** Most labels are mechanical and have no plausible error mode: identity names, formatting, HS texts by definition, ISO and CLDR entries. The categories whose labels need human judgement (P7, the pilot strata) are already fully human-reviewed. The remaining uncertainty is mainly whether generated typos (P3, P5, J4) stay recognisable. A random 60-item sample would spend most of its effort on trivially correct items |
| Human time | ≈ 45–60 min (one reviewer) |
| **Recommendation** | **Defer.** State in the paper that labels are reference- or rule-derived and that rule validity was pilot-checked. Reconsider a *targeted* check of typo items (P3/P5/J4, e.g. 40 items, ≈ 20 min) only if the pilot rejects P02 or P04, or if reviewers question typo recognisability |

## 5. Confirmations
- **Strict DEV tuning rule:** retained exactly as above. If infeasible, this is reported, not relaxed.
- **Fuzzy-matching baseline:** deferred until initial results.
- **Unofficial HS reference:** retained only with the limitations in `experiments/data_provenance.md`. No WCO, legal-text or classification-validation claims.
- **Open Products Facts:** not used (licence not established).
- **Held-out TEST set:**
  - not used for tuning or design decisions; tuning reads DEV only (`tuning.py`);
  - no system has been run on TEST benchmark items (the only system runs so far are the 400 canonical transactions, unit-test examples, and a structural dry-run on DEV items);
  - some human-review items lie in TEST (e.g. P01, P07, P09). The reviewer checks **labels only** and never sees system outputs. Any rule change from the review applies uniformly to all items, so test performance cannot influence design;
  - after freezing, TEST is used exactly once, for the final evaluation.

## 6. What Author 1 must do manually (estimated 25–35 minutes in total)
| # | Task | File(s) | Time |
|---|---|---|---|
| 1 | Review the 10 pilot items: Accept / Reject / Uncertain plus comments | `experiments/pilot_review_sheet.md` → record in `experiments/pilot/pilot_review_sheet_v4.csv` | 15–20 min |
| 2 | P7 Part A: decide the 16 look-alikes (Outside / Potentially in catalogue / Uncertain) | `experiments/p7_review_sheet.md` → `experiments/pilot/p7_lookalike_review_v4.csv` | ≈ 5 min |
| 3 | P7 Part B: scan 100 plain names; list any that could be catalogue items; mark REVIEWED | `experiments/pilot/p7_plain_scan_v4.txt` | 5–8 min |
| 4 | Commit the completed files (or send them), and state explicitly whether the dataset may be frozen | — | 2 min |

Optional: the 60-item label audit (deferred, §4); the catalogue HS plausibility check (optional, stated as a limitation either way).
