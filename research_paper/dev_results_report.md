# LEXITAX AUDIT — DEV Stage Results Report (27 Nov 2026)

**Status: DEV development analysis only. These are not the study's results.** The held-out TEST evaluation has
not been run and requires separate authorisation. S1 was tuned on this DEV split, so S1's DEV numbers are
in-sample and optimistic by construction. They must not be quoted as evidence of generalisation, and no
manuscript claim may rest on them as if they were held-out results.

## 1. Run identity

| Item | Value |
|---|---|
| Branch / commit at run | `research/option-a-evaluation` @ `ce6f98f08a766ef85ba630f0df38723340c85a91` |
| Freeze manifest | `data/generated/MANIFEST.json`, SHA-256 `0d7bddd9c5c8a2855e79d8bfdaff1f81bcc272c2c7744d1c361ce3714ef0b19b` (committed in `453fc55`; verified before and after both stages) |
| Frozen code identity | `1930a0b2b99eb6587879b9b330af93a7eb3d2a3df447dcc1e1c09b22fd44efb6` (38 files; unchanged) |
| Commands (from `research_paper/experiments`, each run once, exit 0) | `python run_all.py --stage tune` (09:53:00–09:53:29 UTC) and `python run_all.py --stage latency` (09:54:30–09:55:11 UTC) |
| Run IDs | None. Run IDs exist only for TEST runs; the DEV stages write exclusive-create outputs that are never overwritten |
| Environment | Python 3.13.18; packages pinned by `requirements.txt` (all installed at the pinned versions; full list in `results/dev_stage_logs/pip_freeze.txt`); 4-CPU Intel Xeon @ 2.10 GHz shared cloud VM, 16 GB |
| Outputs committed in | `b0248b7` (18 files, unedited; SHA-256 of each in `results/dev_stage_record.json`) |
| Failed, repeated or discarded runs | None |
| Warnings | None printed by either stage (console logs in `results/dev_stage_logs/`) |
| TEST | Not loaded, scored or timed. All 2,775 raw output rows (3 systems × 925 items) and all 925 scored items carry split `dev`; no `results/runs/` or `results/test_runs.jsonl` exists |

DEV workloads: 270 product items (198 in the pooled P1–P7 scope, 154 in the P2–P7 selection scope, 72 P8) and
655 country items (348 in the pooled held-out J4–J7 scope). The 18 malformed inputs are not split; they were
evaluated here and are not held out.

## 2. S1 tuning (pre-declared strict rule, unchanged)

Rule (`config.json` `tuning_rule`): maximise DEV macro decision accuracy over P2–P7 subject to DEV macro
silent-error rate ≤ that of B on DEV; ties → larger coverage threshold, fewer typo edits, longer minimum length.

- B on DEV (P2–P7 macro): decision accuracy 0.309, silent-error rate 0.278.
- **All 49 grid settings satisfy the constraint** (the most permissive has SER 0.0186), so the feasible branch of
  the rule applied. No fallback was needed.
- Highest DEV macro accuracy: **1.000** with SER **0.000**, reached by **7 settings**: typo edits 1, minimum
  length 4, any coverage threshold.
- **Selected: `product_min_coverage = 1.0`, `product_typo_max_edits = 1`, `product_typo_min_len = 4`**, by the
  first tie-break (larger coverage threshold). I re-applied the rule independently to the recorded grid and
  obtained the same setting.
- **The coverage threshold had no effect on DEV.** Within every typo setting, all seven threshold values give
  identical DEV results, so the threshold choice is decided only by the tie-break, not by DEV evidence. How it
  behaves on TEST is untested.
- Typo setting effect on DEV (macro accuracy / SER): no typo tier 0.754 / 0; 1 edit, length 4/5/6: 1.000 / 0,
  0.958 / 0, 0.912 / 0; 2 edits, length 4/5/6: 0.978 / 0.019, 0.936 / 0.019, 0.901 / 0.007.
- Full-pipeline DEV grid (`results/dev/grid_full_pipeline_dev.json`): the full pipeline agrees with the
  resolver-level selection at every one of the 49 settings (`n_settings_with_differences = 0`); the S1
  system point coincides with the selected grid point (coverage 0.773, selective risk 0.000).

Selection evidence: `results/tuning_dev.json` (rule text, all 49 settings, B's DEV values, DEV item-ID hash
`6972269c…`).

## 3. How to read the tables

- Outcomes: correct, safe abstention, over-abstention, explicit failure, silent error. Coverage = (correct +
  silent error) / n; decision accuracy = (correct + safe abstention) / n; silent-error rate = silent errors / n;
  selective accuracy = correct / answered.
- **Intervals:** 95 % cluster bootstrap (10,000 resamples of clusters). Clusters, not items, are the
  independent units: for example the pooled product scope has 198 items in only 53 clusters, and the pooled
  country scope has 348 items in 91 clusters. Item-level Wilson intervals are in the CSV files as secondary.
- **Paired tests** are cluster-level sign-flip permutation tests with Holm correction over the 18 primary tests.
  On DEV they are descriptive only: S1's parameters were selected on these same items.
- Small categories (P4, P5, P6, J6, J7) are descriptive only.
- **Latency repetitions are repeated measurements of the same inputs, not independent examples.** Their
  intervals describe run-to-run variability on this machine only.

## 4. Observations (DEV; descriptive)

1. **Product.** S0 answers every pooled item (coverage 1.000) with silent-error rate 0.328 [0.262, 0.420]: every
   P4 short form, P6 ambiguous word and P7 outside-catalogue item gets an answer, and 66 of 72 P8 formal HS
   texts are silent errors. B answers less (0.429) with silent-error rate 0.091 [0.062, 0.120], all from P4 and
   P6. Tuned S1 has decision accuracy 1.000 and no silent errors on DEV, with coverage 0.773; this is in-sample.
2. **P8 (separate category).** S1 and B both have decision accuracy 0.736: 53 safe abstentions and 19
   over-abstentions (in-catalogue HS codes given in formal HS wording are not resolved). S0: 0.083, with 66
   silent errors.
3. **Country identification on held-out forms (J4–J7).** No system identifies any typo (J4) or localised CLDR
   name (J5) correctly. S1 and B abstain on all of them (S1's alias table does not contain these forms, by
   design); S0 produces 12 silent errors (10 on J5, 2 on J6). On the in-table forms J1–J3, S1 identifies all
   items; B identifies only J1 table names (26 of 39), and S0 identifies 53 of 307 with 25 silent errors on J2–J3.
4. **Tax-data behaviour (J4–J7).** B and S0 compute landed costs for every item. 344 of 348 (silent-error rate
   0.989 [0.963, 1.000]) use the wrong rates: for B all 344 are the silent default rates; for S0, 332 default
   rates and 12 another country's rates. Their 4 "correct" items have the right rates with a wrong or missing
   country (masked errors). S1 has no silent errors; it refuses 278
   items correctly and over-refuses 70 items whose jurisdiction has tax data but whose name it could not
   identify (decision accuracy 0.799 [0.690, 0.900]).
5. **Malformed inputs (not held out).** S1 rejects all 18. B computes landed costs for 13 and S0 for 11,
   including negative, infinite and NaN values.
6. **Paired comparisons.** On DEV, 9 of the 18 primary comparisons have Holm-adjusted p < 0.05 (all at
   p_Holm = 0.0018, the floor set by 10,000 permutations): all S0–S1 and B–S1 product and tax-behaviour
   comparisons, and the B–S0 product silent-error comparison. Identification comparisons are not significant
   (p_Holm ≥ 0.25). B and S0 are identical on tax behaviour. These are DEV descriptions, not confirmatory
   tests.
7. **Latency.** Per-call medians: B 0.149 ms, S0 2.108 ms, S1 0.671 ms (product workload); B 0.088 ms, S0
   0.407 ms, S1 0.060 ms (country workload). S1's product timings vary more between repetitions than the others
   (repetition medians 0.441–0.865 ms, IQR 0.198 ms). All values are indicative for this shared VM only.

## 5. Tables (generated directly from the committed output files)

#### Product resolution (pooled = P1–P7; P8 reported separately)

| System | Subset | n | Clusters | Correct | Safe abst. | Over-abst. | Expl. fail. | Silent err. | Coverage [95% cluster CI] | Decision acc. [CI] | Silent-error rate [CI] | Selective acc. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B | **pooled** | 198 | 53 | 67 | 27 | 86 | 0 | 18 | 0.429 [0.381, 0.468] | 0.475 [0.434, 0.531] | 0.091 [0.062, 0.120] | 0.788 |
| B | P1_exact | 44 | 22 | 44 | 0 | 0 | 0 | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 |
| B | P2_format | 44 | 22 | 23 | 0 | 21 | 0 | 0 | 0.523 [0.500, 0.568] | 0.523 [0.500, 0.568] | 0.000 [0.000, 0.000] | 1.000 |
| B | P3_typo | 44 | 22 | 0 | 0 | 44 | 0 | 0 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | – |
| B | P4_short | 14 | 14 | 0 | 0 | 0 | 0 | 14 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 |
| B | P5_confusable | 21 | 11 | 0 | 0 | 21 | 0 | 0 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | – |
| B | P6_ambiguous | 6 | 6 | 0 | 2 | 0 | 0 | 4 | 0.667 [0.333, 1.000] | 0.333 [0.000, 0.667] | 0.667 [0.333, 1.000] | 0.000 |
| B | P7_outside | 25 | 25 | 0 | 25 | 0 | 0 | 0 | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | – |
| B | P8_hs_formal | 72 | 72 | 0 | 53 | 19 | 0 | 0 | 0.000 [0.000, 0.000] | 0.736 [0.625, 0.833] | 0.000 [0.000, 0.000] | – |
| S0 | **pooled** | 198 | 53 | 133 | 0 | 0 | 0 | 65 | 1.000 [1.000, 1.000] | 0.672 [0.580, 0.738] | 0.328 [0.262, 0.420] | 0.672 |
| S0 | P1_exact | 44 | 22 | 44 | 0 | 0 | 0 | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 |
| S0 | P2_format | 44 | 22 | 41 | 0 | 0 | 0 | 3 | 1.000 [1.000, 1.000] | 0.932 [0.864, 1.000] | 0.068 [0.000, 0.136] | 0.932 |
| S0 | P3_typo | 44 | 22 | 32 | 0 | 0 | 0 | 12 | 1.000 [1.000, 1.000] | 0.727 [0.545, 0.886] | 0.273 [0.114, 0.455] | 0.727 |
| S0 | P4_short | 14 | 14 | 0 | 0 | 0 | 0 | 14 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 |
| S0 | P5_confusable | 21 | 11 | 16 | 0 | 0 | 0 | 5 | 1.000 [1.000, 1.000] | 0.762 [0.619, 0.905] | 0.238 [0.095, 0.381] | 0.762 |
| S0 | P6_ambiguous | 6 | 6 | 0 | 0 | 0 | 0 | 6 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 |
| S0 | P7_outside | 25 | 25 | 0 | 0 | 0 | 0 | 25 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 |
| S0 | P8_hs_formal | 72 | 72 | 6 | 0 | 0 | 0 | 66 | 1.000 [1.000, 1.000] | 0.083 [0.028, 0.153] | 0.917 [0.847, 0.972] | 0.083 |
| S1 | **pooled** | 198 | 53 | 153 | 45 | 0 | 0 | 0 | 0.773 [0.685, 0.831] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 |
| S1 | P1_exact | 44 | 22 | 44 | 0 | 0 | 0 | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 |
| S1 | P2_format | 44 | 22 | 44 | 0 | 0 | 0 | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 |
| S1 | P3_typo | 44 | 22 | 44 | 0 | 0 | 0 | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 |
| S1 | P4_short | 14 | 14 | 0 | 14 | 0 | 0 | 0 | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | – |
| S1 | P5_confusable | 21 | 11 | 21 | 0 | 0 | 0 | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 |
| S1 | P6_ambiguous | 6 | 6 | 0 | 6 | 0 | 0 | 0 | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | – |
| S1 | P7_outside | 25 | 25 | 0 | 25 | 0 | 0 | 0 | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | – |
| S1 | P8_hs_formal | 72 | 72 | 0 | 53 | 19 | 0 | 0 | 0.000 [0.000, 0.000] | 0.736 [0.625, 0.833] | 0.000 [0.000, 0.000] | – |

#### Country identification (pooled = held-out forms J4–J7)

| System | Subset | n | Clusters | Correct | Safe abst. | Over-abst. | Expl. fail. | Silent err. | Coverage [95% cluster CI] | Decision acc. [CI] | Silent-error rate [CI] | Selective acc. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B | **pooled** | 348 | 91 | 0 | 14 | 334 | 0 | 0 | 0.000 [0.000, 0.000] | 0.040 [0.021, 0.067] | 0.000 [0.000, 0.000] | – |
| B | J1_table | 39 | 13 | 26 | 0 | 13 | 0 | 0 | 0.667 [0.667, 0.667] | 0.667 [0.667, 0.667] | 0.000 [0.000, 0.000] | 1.000 |
| B | J2_iso_code | 154 | 77 | 0 | 0 | 154 | 0 | 0 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | – |
| B | J3_iso_name | 114 | 74 | 0 | 0 | 114 | 0 | 0 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | – |
| B | J4_typo | 77 | 77 | 0 | 0 | 77 | 0 | 0 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | – |
| B | J5_cldr | 257 | 67 | 0 | 0 | 257 | 0 | 0 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | – |
| B | J6_ambiguous | 6 | 6 | 0 | 6 | 0 | 0 | 0 | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | – |
| B | J7_region | 8 | 8 | 0 | 8 | 0 | 0 | 0 | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | – |
| S0 | **pooled** | 348 | 91 | 0 | 12 | 324 | 0 | 12 | 0.034 [0.008, 0.067] | 0.034 [0.017, 0.058] | 0.034 [0.008, 0.067] | 0.000 |
| S0 | J1_table | 39 | 13 | 35 | 0 | 4 | 0 | 0 | 0.897 [0.821, 0.974] | 0.897 [0.821, 0.974] | 0.000 [0.000, 0.000] | 1.000 |
| S0 | J2_iso_code | 154 | 77 | 10 | 0 | 121 | 0 | 23 | 0.214 [0.143, 0.286] | 0.065 [0.019, 0.123] | 0.149 [0.091, 0.208] | 0.303 |
| S0 | J3_iso_name | 114 | 74 | 8 | 0 | 104 | 0 | 2 | 0.088 [0.041, 0.147] | 0.070 [0.026, 0.124] | 0.018 [0.000, 0.045] | 0.800 |
| S0 | J4_typo | 77 | 77 | 0 | 0 | 77 | 0 | 0 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | – |
| S0 | J5_cldr | 257 | 67 | 0 | 0 | 247 | 0 | 10 | 0.039 [0.004, 0.079] | 0.000 [0.000, 0.000] | 0.039 [0.004, 0.079] | 0.000 |
| S0 | J6_ambiguous | 6 | 6 | 0 | 4 | 0 | 0 | 2 | 0.333 [0.000, 0.667] | 0.667 [0.333, 1.000] | 0.333 [0.000, 0.667] | 0.000 |
| S0 | J7_region | 8 | 8 | 0 | 8 | 0 | 0 | 0 | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | – |
| S1 | **pooled** | 348 | 91 | 0 | 14 | 334 | 0 | 0 | 0.000 [0.000, 0.000] | 0.040 [0.021, 0.067] | 0.000 [0.000, 0.000] | – |
| S1 | J1_table | 39 | 13 | 39 | 0 | 0 | 0 | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 |
| S1 | J2_iso_code | 154 | 77 | 154 | 0 | 0 | 0 | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 |
| S1 | J3_iso_name | 114 | 74 | 114 | 0 | 0 | 0 | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 |
| S1 | J4_typo | 77 | 77 | 0 | 0 | 77 | 0 | 0 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | – |
| S1 | J5_cldr | 257 | 67 | 0 | 0 | 257 | 0 | 0 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | – |
| S1 | J6_ambiguous | 6 | 6 | 0 | 6 | 0 | 0 | 0 | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | – |
| S1 | J7_region | 8 | 8 | 0 | 8 | 0 | 0 | 0 | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | – |

#### Tax-data behaviour: compute with the true rates or refuse (pooled = J4–J7)

| System | Subset | n | Clusters | Correct | Safe abst. | Over-abst. | Expl. fail. | Silent err. | Coverage [95% cluster CI] | Decision acc. [CI] | Silent-error rate [CI] | Selective acc. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B | **pooled** | 348 | 91 | 4 | 0 | 0 | 0 | 344 | 1.000 [1.000, 1.000] | 0.011 [0.000, 0.037] | 0.989 [0.963, 1.000] | 0.011 |
| B | J1_table | 39 | 13 | 27 | 0 | 0 | 0 | 12 | 1.000 [1.000, 1.000] | 0.692 [0.667, 0.744] | 0.308 [0.256, 0.333] | 0.692 |
| B | J2_iso_code | 154 | 77 | 2 | 0 | 0 | 0 | 152 | 1.000 [1.000, 1.000] | 0.013 [0.000, 0.039] | 0.987 [0.961, 1.000] | 0.013 |
| B | J3_iso_name | 114 | 74 | 0 | 0 | 0 | 0 | 114 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 |
| B | J4_typo | 77 | 77 | 1 | 0 | 0 | 0 | 76 | 1.000 [1.000, 1.000] | 0.013 [0.000, 0.039] | 0.987 [0.961, 1.000] | 0.013 |
| B | J5_cldr | 257 | 67 | 3 | 0 | 0 | 0 | 254 | 1.000 [1.000, 1.000] | 0.012 [0.000, 0.038] | 0.988 [0.962, 1.000] | 0.012 |
| B | J6_ambiguous | 6 | 6 | 0 | 0 | 0 | 0 | 6 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 |
| B | J7_region | 8 | 8 | 0 | 0 | 0 | 0 | 8 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 |
| S0 | **pooled** | 348 | 91 | 4 | 0 | 0 | 0 | 344 | 1.000 [1.000, 1.000] | 0.011 [0.000, 0.037] | 0.989 [0.963, 1.000] | 0.011 |
| S0 | J1_table | 39 | 13 | 35 | 0 | 0 | 0 | 4 | 1.000 [1.000, 1.000] | 0.897 [0.821, 0.974] | 0.103 [0.026, 0.179] | 0.897 |
| S0 | J2_iso_code | 154 | 77 | 10 | 0 | 0 | 0 | 144 | 1.000 [1.000, 1.000] | 0.065 [0.019, 0.123] | 0.935 [0.877, 0.981] | 0.065 |
| S0 | J3_iso_name | 114 | 74 | 8 | 0 | 0 | 0 | 106 | 1.000 [1.000, 1.000] | 0.070 [0.026, 0.124] | 0.930 [0.876, 0.974] | 0.070 |
| S0 | J4_typo | 77 | 77 | 1 | 0 | 0 | 0 | 76 | 1.000 [1.000, 1.000] | 0.013 [0.000, 0.039] | 0.987 [0.961, 1.000] | 0.013 |
| S0 | J5_cldr | 257 | 67 | 3 | 0 | 0 | 0 | 254 | 1.000 [1.000, 1.000] | 0.012 [0.000, 0.038] | 0.988 [0.962, 1.000] | 0.012 |
| S0 | J6_ambiguous | 6 | 6 | 0 | 0 | 0 | 0 | 6 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 |
| S0 | J7_region | 8 | 8 | 0 | 0 | 0 | 0 | 8 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 |
| S1 | **pooled** | 348 | 91 | 0 | 278 | 70 | 0 | 0 | 0.000 [0.000, 0.000] | 0.799 [0.690, 0.900] | 0.000 [0.000, 0.000] | – |
| S1 | J1_table | 39 | 13 | 39 | 0 | 0 | 0 | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 |
| S1 | J2_iso_code | 154 | 77 | 26 | 128 | 0 | 0 | 0 | 0.169 [0.091, 0.260] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 |
| S1 | J3_iso_name | 114 | 74 | 11 | 103 | 0 | 0 | 0 | 0.096 [0.043, 0.162] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 |
| S1 | J4_typo | 77 | 77 | 0 | 64 | 13 | 0 | 0 | 0.000 [0.000, 0.000] | 0.831 [0.740, 0.909] | 0.000 [0.000, 0.000] | – |
| S1 | J5_cldr | 257 | 67 | 0 | 200 | 57 | 0 | 0 | 0.000 [0.000, 0.000] | 0.778 [0.656, 0.884] | 0.000 [0.000, 0.000] | – |
| S1 | J6_ambiguous | 6 | 6 | 0 | 6 | 0 | 0 | 0 | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | – |
| S1 | J7_region | 8 | 8 | 0 | 8 | 0 | 0 | 0 | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | – |

#### Paired comparisons (DEV; pooled scopes; cluster sign-flip permutation, 10,000 permutations; Holm over the 18 tests)

| Task | Metric | A → B | Items | Clusters | Rate A | Rate B | Diff (B−A) [95% cluster CI] | p | p (Holm) | McNemar discordant (A✗B✓ / A✓B✗) | McNemar p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| product | decision_correct | B → S0 | 198 | 53 | 0.475 | 0.672 | +0.197 [+0.058, +0.290] | 0.0181 | 0.1629 | 66 / 27 | 6.467e-05 |
| product | silent_error | B → S0 | 198 | 53 | 0.091 | 0.328 | +0.237 [+0.169, +0.329] | 9.999e-05 | 0.0018 | 47 / 0 | 1.421e-14 |
| product | decision_correct | S0 → S1 | 198 | 53 | 0.672 | 1.000 | +0.328 [+0.262, +0.418] | 9.999e-05 | 0.0018 | 65 / 0 | 5.421e-20 |
| product | silent_error | S0 → S1 | 198 | 53 | 0.328 | 0.000 | -0.328 [-0.418, -0.262] | 9.999e-05 | 0.0018 | 0 / 65 | 5.421e-20 |
| product | decision_correct | B → S1 | 198 | 53 | 0.475 | 1.000 | +0.525 [+0.469, +0.566] | 9.999e-05 | 0.0018 | 104 / 0 | 9.861e-32 |
| product | silent_error | B → S1 | 198 | 53 | 0.091 | 0.000 | -0.091 [-0.121, -0.063] | 9.999e-05 | 0.0018 | 0 / 18 | 7.629e-06 |
| identification | decision_correct | B → S0 | 348 | 91 | 0.040 | 0.034 | -0.006 [-0.015, +0.000] | 0.5 | 1 | 0 / 2 | 0.5 |
| identification | silent_error | B → S0 | 348 | 91 | 0.000 | 0.034 | +0.034 [+0.009, +0.067] | 0.03125 | 0.25 | 12 / 0 | 0.0004883 |
| identification | decision_correct | S0 → S1 | 348 | 91 | 0.034 | 0.040 | +0.006 [+0.000, +0.015] | 0.5 | 1 | 2 / 0 | 0.5 |
| identification | silent_error | S0 → S1 | 348 | 91 | 0.034 | 0.000 | -0.034 [-0.067, -0.009] | 0.03125 | 0.25 | 0 / 12 | 0.0004883 |
| identification | decision_correct | B → S1 | 348 | 91 | 0.040 | 0.040 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| identification | silent_error | B → S1 | 348 | 91 | 0.000 | 0.000 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| tax_behaviour | decision_correct | B → S0 | 348 | 91 | 0.011 | 0.011 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| tax_behaviour | silent_error | B → S0 | 348 | 91 | 0.989 | 0.989 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| tax_behaviour | decision_correct | S0 → S1 | 348 | 91 | 0.011 | 0.799 | +0.787 [+0.676, +0.889] | 9.999e-05 | 0.0018 | 278 / 4 | 6.735e-77 |
| tax_behaviour | silent_error | S0 → S1 | 348 | 91 | 0.989 | 0.000 | -0.989 [-1.000, -0.963] | 9.999e-05 | 0.0018 | 0 / 344 | 5.581e-104 |
| tax_behaviour | decision_correct | B → S1 | 348 | 91 | 0.011 | 0.799 | +0.787 [+0.676, +0.889] | 9.999e-05 | 0.0018 | 278 / 4 | 6.735e-77 |
| tax_behaviour | silent_error | B → S1 | 348 | 91 | 0.989 | 0.000 | -0.989 [-1.000, -0.963] | 9.999e-05 | 0.0018 | 0 / 344 | 5.581e-104 |

#### Malformed inputs (18 items; not split, so not held out)

| System | Rejected | Status counts | Landed costs computed for malformed input |
|---|---|---|---|
| B | 5/18 | ERROR 5, OK 13 | 13: -2985.4, -129.8, 129.8, 129.8, 1963.5, 1963.5, 2063.82, 2206.6, 2206.6, 2206.6, nan, nan, inf |
| S0 | 7/18 | ERROR 7, OK 11 | 11: -2985.4, -129.8, 129.8, 129.8, 2063.82, 2206.6, 2206.6, 2206.6, nan, nan, inf |
| S1 | 18/18 | INVALID 18 | 0: none |

#### Tuning grid (resolver-level DEV macro over P2–P7; B: accuracy 0.309, silent-error rate 0.278)

| Coverage threshold | Typo edits | Min length | DEV macro accuracy | DEV macro SER | Feasible (SER ≤ B) | Pooled P1–P7 coverage | Pooled selective risk |
|---|---|---|---|---|---|---|---|
| 1.0 **(selected)** | 1 | 4 | 1.0000 | 0.0000 | yes | 0.773 | 0.000 |
| 0.75 | 1 | 4 | 1.0000 | 0.0000 | yes | 0.773 | 0.000 |
| 0.67 | 1 | 4 | 1.0000 | 0.0000 | yes | 0.773 | 0.000 |
| 0.5 | 1 | 4 | 1.0000 | 0.0000 | yes | 0.773 | 0.000 |
| 0.34 | 1 | 4 | 1.0000 | 0.0000 | yes | 0.773 | 0.000 |
| 0.25 | 1 | 4 | 1.0000 | 0.0000 | yes | 0.773 | 0.000 |
| 0.0 | 1 | 4 | 1.0000 | 0.0000 | yes | 0.773 | 0.000 |
| 1.0 | 2 | 4 | 0.9776 | 0.0186 | yes | 0.778 | 0.013 |
| 0.75 | 2 | 4 | 0.9776 | 0.0186 | yes | 0.778 | 0.013 |
| 0.67 | 2 | 4 | 0.9776 | 0.0186 | yes | 0.778 | 0.013 |
| 0.5 | 2 | 4 | 0.9776 | 0.0186 | yes | 0.778 | 0.013 |
| 0.34 | 2 | 4 | 0.9776 | 0.0186 | yes | 0.778 | 0.013 |
| 0.25 | 2 | 4 | 0.9776 | 0.0186 | yes | 0.778 | 0.013 |
| 0.0 | 2 | 4 | 0.9776 | 0.0186 | yes | 0.778 | 0.013 |
| 1.0 | 1 | 5 | 0.9580 | 0.0000 | yes | 0.722 | 0.000 |
| 0.75 | 1 | 5 | 0.9580 | 0.0000 | yes | 0.722 | 0.000 |
| 0.67 | 1 | 5 | 0.9580 | 0.0000 | yes | 0.722 | 0.000 |
| 0.5 | 1 | 5 | 0.9580 | 0.0000 | yes | 0.722 | 0.000 |
| 0.34 | 1 | 5 | 0.9580 | 0.0000 | yes | 0.722 | 0.000 |
| 0.25 | 1 | 5 | 0.9580 | 0.0000 | yes | 0.722 | 0.000 |
| 0.0 | 1 | 5 | 0.9580 | 0.0000 | yes | 0.722 | 0.000 |
| 1.0 | 2 | 5 | 0.9356 | 0.0186 | yes | 0.727 | 0.014 |
| 0.75 | 2 | 5 | 0.9356 | 0.0186 | yes | 0.727 | 0.014 |
| 0.67 | 2 | 5 | 0.9356 | 0.0186 | yes | 0.727 | 0.014 |
| 0.5 | 2 | 5 | 0.9356 | 0.0186 | yes | 0.727 | 0.014 |
| 0.34 | 2 | 5 | 0.9356 | 0.0186 | yes | 0.727 | 0.014 |
| 0.25 | 2 | 5 | 0.9356 | 0.0186 | yes | 0.727 | 0.014 |
| 0.0 | 2 | 5 | 0.9356 | 0.0186 | yes | 0.727 | 0.014 |
| 1.0 | 1 | 6 | 0.9118 | 0.0000 | yes | 0.672 | 0.000 |
| 0.75 | 1 | 6 | 0.9118 | 0.0000 | yes | 0.672 | 0.000 |
| 0.67 | 1 | 6 | 0.9118 | 0.0000 | yes | 0.672 | 0.000 |
| 0.5 | 1 | 6 | 0.9118 | 0.0000 | yes | 0.672 | 0.000 |
| 0.34 | 1 | 6 | 0.9118 | 0.0000 | yes | 0.672 | 0.000 |
| 0.25 | 1 | 6 | 0.9118 | 0.0000 | yes | 0.672 | 0.000 |
| 0.0 | 1 | 6 | 0.9118 | 0.0000 | yes | 0.672 | 0.000 |
| 1.0 | 2 | 6 | 0.9013 | 0.0067 | yes | 0.672 | 0.008 |
| 0.75 | 2 | 6 | 0.9013 | 0.0067 | yes | 0.672 | 0.008 |
| 0.67 | 2 | 6 | 0.9013 | 0.0067 | yes | 0.672 | 0.008 |
| 0.5 | 2 | 6 | 0.9013 | 0.0067 | yes | 0.672 | 0.008 |
| 0.34 | 2 | 6 | 0.9013 | 0.0067 | yes | 0.672 | 0.008 |
| 0.25 | 2 | 6 | 0.9013 | 0.0067 | yes | 0.672 | 0.008 |
| 0.0 | 2 | 6 | 0.9013 | 0.0067 | yes | 0.672 | 0.008 |
| 1.0 | 0 | 4 | 0.7540 | 0.0000 | yes | 0.500 | 0.000 |
| 0.75 | 0 | 4 | 0.7540 | 0.0000 | yes | 0.500 | 0.000 |
| 0.67 | 0 | 4 | 0.7540 | 0.0000 | yes | 0.500 | 0.000 |
| 0.5 | 0 | 4 | 0.7540 | 0.0000 | yes | 0.500 | 0.000 |
| 0.34 | 0 | 4 | 0.7540 | 0.0000 | yes | 0.500 | 0.000 |
| 0.25 | 0 | 4 | 0.7540 | 0.0000 | yes | 0.500 | 0.000 |
| 0.0 | 0 | 4 | 0.7540 | 0.0000 | yes | 0.500 | 0.000 |

#### Latency (DEV; 200 warm-up calls, then 30 repetitions of each whole workload)

| Workload | System | Calls | Per-call median ms | p95 | p99 | Mean (SD) | Throughput calls/s | Median of 30 repetition medians [bootstrap 95%] | Repetition medians min–max (IQR) |
|---|---|---|---|---|---|---|---|---|---|
| product (270 items) | B | 8100 | 0.149 | 0.266 | 0.363 | 0.160 (0.070) | 6208 | 0.147 [0.146, 0.147] | 0.142–0.234 (0.002) |
| product (270 items) | S0 | 8100 | 2.108 | 3.740 | 4.103 | 1.887 (1.110) | 530 | 2.103 [2.093, 2.122] | 2.071–3.599 (0.056) |
| product (270 items) | S1 | 8100 | 0.671 | 3.571 | 5.931 | 1.067 (1.159) | 936 | 0.524 [0.486, 0.634] | 0.441–0.865 (0.198) |
| country (655 items) | B | 19650 | 0.088 | 0.202 | 0.260 | 0.096 (0.097) | 10318 | 0.084 [0.081, 0.088] | 0.079–0.131 (0.011) |
| country (655 items) | S0 | 19650 | 0.407 | 0.773 | 0.966 | 0.458 (0.196) | 2178 | 0.406 [0.396, 0.419] | 0.377–0.755 (0.032) |
| country (655 items) | S1 | 19650 | 0.060 | 0.411 | 0.716 | 0.113 (0.139) | 8799 | 0.059 [0.059, 0.060] | 0.058–0.099 (0.002) |

## 6. Output files (all under `research_paper/experiments/results/`, committed unedited in `b0248b7`)

| File | Content |
|---|---|
| `tuning_dev.json` | Tuning rule, all 49 settings with DEV macro metrics, B's DEV values, selected setting |
| `dev/grid_full_pipeline_dev.json` | Full-pipeline DEV risk–coverage at all 49 settings (figure and sensitivity only) |
| `dev/figures/dev_risk_coverage.pdf` | DEV risk–coverage figure (S1 grid, selected setting, B/S0/S1 DEV points) |
| `dev/figures/figures_provenance.json` | Figure inputs with SHA-256; S1 system point vs selected grid point |
| `dev/processed/primary_dev_{product,identification,tax_behaviour}_summary.csv` | Per-system, per-category metrics with cluster-bootstrap and Wilson intervals |
| `dev/processed/primary_dev_paired_tests.csv` | 18 primary paired comparisons (permutation p, Holm p, McNemar) |
| `dev/processed/primary_dev_{product,country,malformed}_items.csv` | Per-item outcomes |
| `dev/processed/primary_dev_provenance.json` | Benchmark hashes, split, systems, item counts |
| `dev/raw/primary_dev_outputs.jsonl` | Raw system outputs for all 2,775 DEV item–system pairs |
| `latency_dev.json` | Latency method, environment, per-call and run-to-run statistics, all repetition values |
| `dev_stage_record.json` | Commands, times, commit, manifest hash and SHA-256 of every output above |
| `dev_stage_logs/` | Console output of both stages and the full package list |

## 7. Limitations specific to this DEV report

- S1's parameters were chosen on these items, so S1's DEV results are in-sample. Seven settings tied at DEV
  accuracy 1.000, and the coverage threshold did not affect any DEV result.
- The data are synthetic (catalogue, perturbations, unsourced tax rates); results say nothing about real customs
  declarations or legal classification. HS texts come from an unofficial mirror (`freeze_approval_record.md` §3).
- DEV clusters are few in some categories (P6 6, J6 6, J7 8), and the intervals there are wide or degenerate.
- Latency was measured once on a shared cloud VM; it is indicative only and was never measured on TEST.
