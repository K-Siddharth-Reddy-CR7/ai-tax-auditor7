# LEXITAX AUDIT — Final Held-out TEST Results Report (27 Nov 2026)

**Status: confirmatory TEST results of the single planned TEST run.** The run used the frozen benchmark, code and
configuration and the S1 setting selected on DEV beforehand. Nothing was retuned or changed after TEST outcomes
were seen, and TEST has not been rerun. Section 4 (primary analysis) is confirmatory. Sections 5 (sensitivity) and
6 (ladder and ablations) are secondary or exploratory, as pre-declared. DEV results (`dev_results_report.md`) are
development analysis only.

## 1. Run identity and provenance

| Item | Value |
|---|---|
| Run ID | **`20261127T104925Z-0f293784`** (first and only TEST run; `previous_runs` empty; not a rerun) |
| Command (from `research_paper/experiments`) | `python run_all.py --stage evaluate --split test --authorised-by "Syeda Sayeeda Farhath (Corresponding Author); reason: first planned final held-out TEST evaluation after frozen DEV tuning"` |
| Reason field | The run-control code has no reason field for a first run (`--rerun-reason` is only for reruns and was not used), so the reason is recorded in the `authorised_by` text, which `run.json` and the run log store verbatim |
| Timing | Run opened 2026-11-27T10:49:25.194573Z, closed 2026-11-27T10:51:46.797972Z; wall time 2 min 31 s; exit 0 |
| Status | `completed`, `error: null` (`close.json`); run log `results/test_runs.jsonl` has exactly two entries (started, completed) and reconciles |
| Git | HEAD `0e34002929cb7023addfad10a549d8c111b41bbf`, clean tree; frozen commit `693cb286e68c…` (descendant check: no code-identity path changed) |
| Hashes verified at open (`run.json`) | manifest `0d7bddd9…`; code identity `1930a0b2b99e…`; product `a6a87fc3…`, country `1bf3f489…`, malformed `bb3af788…`, excluded items `fcdc6789…`; config `ba8b5ef7…`; review treatments `cc5f593f…`; evaluation exclusions `2ecacabe…`; tuning record `c0510c3a…` |
| S1 setting | `product_min_coverage = 1.0`, `product_typo_max_edits = 1`, `product_typo_min_len = 4` (from `tuning_dev.json`, loaded with hash check) |
| Environment | CPython 3.13.18; full package list in `run.json` (`environment.packages`); Linux 6.18, 4-CPU Intel Xeon @ 2.10 GHz |
| Outputs | 30 files in `results/runs/20261127T104925Z-0f293784/`; all match the run's own `outputs_sha256.json`; `close.json` binds that inventory. Committed unedited in `e0bf964`. `results/test_stage_record.json` adds the command, times and SHA-256 of every TEST file and of the run log |
| Scored items | Product 529 (pooled P1–P7: 359 items, 134 clusters; P8: 170); country 1,465 (pooled J4–J7: 769 items, 207 clusters); malformed 18 |
| Exclusions | The 8 pilot TEST items were removed centrally by the Phase B choke point and appear in no scored row; they are listed with reasons in `processed/primary_test_excluded_from_metrics.csv` (§D). The 4 P7 benchmark exclusions are absent from the frozen benchmark (`excluded_items.csv`, unchanged) |
| Failures or warnings | None. No error was raised and nothing was printed except the completion line |
| Known issue | The three TEST outcome figures (frozen figure code) draw the overall title over one panel title. The overlap is cosmetic; the plotted data match the summary CSVs |

## 2. How to read the results

- **Outcomes per item:** correct, safe abstention, over-abstention, explicit failure, silent error.
- **Rates:**
  - coverage = (correct + silent error) / n;
  - decision accuracy = (correct + safe abstention) / n;
  - silent-error rate = silent errors / n;
  - selective accuracy = correct / answered;
  - over-abstention rate = over-abstentions / n.

  For tax behaviour, "answered" means a landed cost was computed.
- **Independent units are clusters, not items.** All intervals are 95 % cluster-bootstrap percentile intervals
  (10,000 resamples). Paired tests are cluster-level sign-flip permutation tests (10,000 permutations; the smallest
  attainable Holm-adjusted p for 18 tests is 0.0018). Item-level Wilson intervals and McNemar tests are secondary.
- **Scopes:**
  - pooled product claims use P1–P7; P8 (formal HS texts) is reported separately;
  - pooled country claims use only the held-out forms J4–J7; J1–J3 appear in S1's own alias table, so they
    are solved by construction and reported descriptively;
  - P4, P5, P6, J6 and J7 are small and descriptive only.
- **Synthetic setting.** The catalogue, perturbations and tax rates are synthetic or unsourced, and HS texts come
  from an unofficial mirror. "Correct" means correct against this benchmark's own tables, not legally correct.

## 3. Summary of confirmatory findings

1. **Product resolution (P1–P7, 359 items / 134 clusters).**
   - **S1** answered 68.8 % of items [60.7, 75.1] with **no silent errors** (0.000 [0.000, 0.000]) and decision
     accuracy 0.997 [0.991, 1.000]. Its one error was an over-abstention on a P5 confusable item.
   - **S0** answered every item and was silently wrong on 44.3 % [38.2, 51.2], every P4, P6 and P7 item included.
   - **B** had a silent-error rate of 0.053 [0.034, 0.072], from P4 and P6 only, but over-abstained on 132 items
     (all P3 typos, all P5 confusables, about half of P2).
   - **Holm-significant:** S1 beat both S0 and B on decision accuracy (+0.440 and +0.418) and on silent-error rate
     (−0.443 and −0.053). S0 had more silent errors than B (+0.390).
   - **Not significant:** the original six-stage pipeline S0 was **not** more accurate than the baseline B
     (−0.022 [−0.142, +0.071], Holm p = 1).
2. **P8 formal HS texts (170; separate).** S1 and B both have decision accuracy 0.859: 146 safe abstentions and
   24 over-abstentions, the in-catalogue codes worded formally. S0 was silently wrong on 167 of 170 (0.982).
3. **Country identification on held-out forms (J4–J7, 769 / 207).**
   - **No system identified any held-out form correctly**, apart from 3 J5 items for S0.
   - S1 and B abstain on all J4/J5 items: over-abstention 734 of 769 (0.954) each, and decision accuracy 0.046
     (only the J6/J7 no-country items).
   - S0 makes 12 silent errors (0.016 [0.005, 0.029]).
   - **No identification comparison is Holm-significant:** S0 vs S1 silent error p = 0.0078 unadjusted, Holm
     0.070. B and S1 behave identically on these forms.
   - S1's ISO identification helps only on the in-table forms J1–J3 (all 696 correct), which are excluded from
     pooled claims by design. **This is an unfavourable result for S1's identification stage on held-out forms.**
4. **Tax-data behaviour (J4–J7, 769 / 207).**
   - **B and S0 computed a landed cost for every item, and almost all were wrong** (silent-error rates 1.000 and
     0.996 [0.991, 1.000]).
   - **S1 computed none.** It correctly refused 632 items whose true jurisdiction has no tax data and over-refused
     137 (0.178) that do. Its decision accuracy is 0.822 [0.755, 0.883] with no silent errors.
   - Both S1 comparisons are Holm-significant (+0.818 vs S0, +0.822 vs B). B and S0 do not differ.
   - **S1's tax-behaviour advantage comes entirely from refusal (coverage 0 on held-out forms), not from computing
     correct costs.**
5. **Error propagation** (tabulated from per-item classifications, §A6).
   - **Product errors never changed duty, VAT or landed cost**, for any system. In the original tables the duty
     and VAT rates depend only on the country (`taxes.json`, read by `tax_agent`), so with the country fixed a
     wrong product cannot change the cost.
   - Product errors surface instead as wrong or invented classifications and policy records. S0 fabricated an HS
     code for 120 of 359 pooled items and 88 of 170 P8 items, and attached a wrong policy record to 14 and 11.
   - Country errors do propagate. B and S0 both returned silent landed-cost errors: 137 and 134 items, all at the
     default 5 % duty / 10 % VAT. The median relative error is 10.3 %, the maximum 13.75 %. Both also computed a
     cost for all 632 items that should have been refused, all at default rates except 12 of S0's, which used
     another country's rates.
   - S1 refused all 769; none of its outputs carried a cost error.
6. **Malformed inputs (18; not held out, same items as DEV).** S1 rejected all 18. B computed landed costs for 13
   and S0 for 11, including negative (−129.8, −2,985.4), infinite and NaN values.
7. **Counts.** 9 of the 18 primary tests are Holm-significant, all in favour of S1 or against S0: product 5, tax
   behaviour 4, identification 0.
8. **Sensitivity (secondary).** Removing the sibling clusters of the 8 excluded items (18 product and 9 country
   items) changes no conclusion. The same 9 tests are Holm-significant, and S1's pooled product decision accuracy
   becomes 1.000 (341 / 131).

## 3a. DEV versus TEST for S1 (descriptive)

- **Product (pooled P1–P7):** decision accuracy 1.000 on DEV (in-sample) and 0.997 on TEST; silent-error rate 0
  on both. Coverage was 0.773 on DEV and 0.688 on TEST. Coverage depends on the category mix: P7 items, which
  should be declined, are 86 of 359 TEST items but 25 of 198 DEV items.
- **Tax behaviour:** decision accuracy 0.799 on DEV and 0.822 on TEST.
- **Identification:** the same pattern on both splits.
- **Coverage threshold:** it had no effect on any DEV result. On TEST, the exploratory ablation without the
  coverage guard produced silent errors that S1 avoids: 1 in pooled P1–P7 (a P7 item) and 13 on P8 (§C1;
  exploratory).

## 4–6. Tables (generated directly from the committed run outputs)

Section labels: A = primary (confirmatory), B = secondary sensitivity, C = exploratory, D = exclusions audit.

### A. Primary (confirmatory) results


#### A1. Product resolution (pooled = P1–P7; P8 formal HS texts reported separately, not pooled)

| System | Subset | n | Clusters | Correct | Safe abst. | Over-abst. | Expl. fail. | Silent err. | Coverage [95% cluster CI] | Decision acc. [CI] | Silent-error rate [CI] | Selective acc. | Over-abst. rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B | **pooled** | 359 | 134 | 116 | 92 | 132 | 0 | 19 | 0.376 [0.334, 0.412] | 0.579 [0.539, 0.633] | 0.053 [0.034, 0.072] | 0.859 | 0.368 |
| B | P1_exact | 76 | 38 | 76 | 0 | 0 | 0 | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.000 |
| B | P2_format | 75 | 38 | 40 | 0 | 35 | 0 | 0 | 0.533 [0.500, 0.575] | 0.533 [0.500, 0.575] | 0.000 [0.000, 0.000] | 1.000 | 0.467 |
| B | P3_typo | 75 | 38 | 0 | 0 | 75 | 0 | 0 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | – | 1.000 |
| B | P4_short | 15 | 15 | 0 | 0 | 0 | 0 | 15 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 | 0.000 |
| B | P5_confusable | 22 | 12 | 0 | 0 | 22 | 0 | 0 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | – | 1.000 |
| B | P6_ambiguous | 10 | 10 | 0 | 6 | 0 | 0 | 4 | 0.400 [0.100, 0.700] | 0.600 [0.300, 0.900] | 0.400 [0.100, 0.700] | 0.000 | 0.000 |
| B | P7_outside | 86 | 86 | 0 | 86 | 0 | 0 | 0 | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | – | 0.000 |
| B | P8_hs_formal | 170 | 170 | 0 | 146 | 24 | 0 | 0 | 0.000 [0.000, 0.000] | 0.859 [0.806, 0.912] | 0.000 [0.000, 0.000] | – | 0.141 |
| S0 | **pooled** | 359 | 134 | 200 | 0 | 0 | 0 | 159 | 1.000 [1.000, 1.000] | 0.557 [0.488, 0.618] | 0.443 [0.382, 0.512] | 0.557 | 0.000 |
| S0 | P1_exact | 76 | 38 | 76 | 0 | 0 | 0 | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.000 |
| S0 | P2_format | 75 | 38 | 68 | 0 | 0 | 0 | 7 | 1.000 [1.000, 1.000] | 0.907 [0.840, 0.961] | 0.093 [0.039, 0.160] | 0.907 | 0.000 |
| S0 | P3_typo | 75 | 38 | 41 | 0 | 0 | 0 | 34 | 1.000 [1.000, 1.000] | 0.547 [0.395, 0.693] | 0.453 [0.307, 0.605] | 0.547 | 0.000 |
| S0 | P4_short | 15 | 15 | 0 | 0 | 0 | 0 | 15 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 | 0.000 |
| S0 | P5_confusable | 22 | 12 | 15 | 0 | 0 | 0 | 7 | 1.000 [1.000, 1.000] | 0.682 [0.565, 0.842] | 0.318 [0.158, 0.435] | 0.682 | 0.000 |
| S0 | P6_ambiguous | 10 | 10 | 0 | 0 | 0 | 0 | 10 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 | 0.000 |
| S0 | P7_outside | 86 | 86 | 0 | 0 | 0 | 0 | 86 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 | 0.000 |
| S0 | P8_hs_formal | 170 | 170 | 3 | 0 | 0 | 0 | 167 | 1.000 [1.000, 1.000] | 0.018 [0.000, 0.041] | 0.982 [0.959, 1.000] | 0.018 | 0.000 |
| S1 | **pooled** | 359 | 134 | 247 | 111 | 1 | 0 | 0 | 0.688 [0.607, 0.751] | 0.997 [0.991, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.003 |
| S1 | P1_exact | 76 | 38 | 76 | 0 | 0 | 0 | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.000 |
| S1 | P2_format | 75 | 38 | 75 | 0 | 0 | 0 | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.000 |
| S1 | P3_typo | 75 | 38 | 75 | 0 | 0 | 0 | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.000 |
| S1 | P4_short | 15 | 15 | 0 | 15 | 0 | 0 | 0 | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | – | 0.000 |
| S1 | P5_confusable | 22 | 12 | 21 | 0 | 1 | 0 | 0 | 0.955 [0.857, 1.000] | 0.955 [0.857, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.045 |
| S1 | P6_ambiguous | 10 | 10 | 0 | 10 | 0 | 0 | 0 | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | – | 0.000 |
| S1 | P7_outside | 86 | 86 | 0 | 86 | 0 | 0 | 0 | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | – | 0.000 |
| S1 | P8_hs_formal | 170 | 170 | 0 | 146 | 24 | 0 | 0 | 0.000 [0.000, 0.000] | 0.859 [0.806, 0.912] | 0.000 [0.000, 0.000] | – | 0.141 |

#### A2. Country identification (pooled = held-out forms J4–J7; J1–J3 are in S1's own table and are descriptive only)

| System | Subset | n | Clusters | Correct | Safe abst. | Over-abst. | Expl. fail. | Silent err. | Coverage [95% cluster CI] | Decision acc. [CI] | Silent-error rate [CI] | Selective acc. | Over-abst. rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B | **pooled** | 769 | 207 | 0 | 35 | 734 | 0 | 0 | 0.000 [0.000, 0.000] | 0.046 [0.030, 0.063] | 0.000 [0.000, 0.000] | – | 0.954 |
| B | J1_table | 81 | 27 | 54 | 0 | 27 | 0 | 0 | 0.667 [0.667, 0.667] | 0.667 [0.667, 0.667] | 0.000 [0.000, 0.000] | 1.000 | 0.333 |
| B | J2_iso_code | 344 | 172 | 0 | 0 | 344 | 0 | 0 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | – | 1.000 |
| B | J3_iso_name | 271 | 168 | 0 | 0 | 271 | 0 | 0 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | – | 1.000 |
| B | J4_typo | 170 | 170 | 0 | 0 | 170 | 0 | 0 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | – | 1.000 |
| B | J5_cldr | 564 | 147 | 0 | 0 | 564 | 0 | 0 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | – | 1.000 |
| B | J6_ambiguous | 9 | 9 | 0 | 9 | 0 | 0 | 0 | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | – | 0.000 |
| B | J7_region | 26 | 26 | 0 | 26 | 0 | 0 | 0 | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | – | 0.000 |
| S0 | **pooled** | 769 | 207 | 3 | 30 | 724 | 0 | 12 | 0.020 [0.008, 0.034] | 0.043 [0.028, 0.059] | 0.016 [0.005, 0.029] | 0.200 | 0.941 |
| S0 | J1_table | 81 | 27 | 78 | 0 | 3 | 0 | 0 | 0.963 [0.926, 1.000] | 0.963 [0.926, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.037 |
| S0 | J2_iso_code | 344 | 172 | 19 | 0 | 283 | 0 | 42 | 0.177 [0.131, 0.227] | 0.055 [0.026, 0.087] | 0.122 [0.087, 0.160] | 0.311 | 0.823 |
| S0 | J3_iso_name | 271 | 168 | 15 | 0 | 251 | 0 | 5 | 0.074 [0.044, 0.107] | 0.055 [0.030, 0.085] | 0.018 [0.004, 0.036] | 0.750 | 0.926 |
| S0 | J4_typo | 170 | 170 | 0 | 0 | 169 | 0 | 1 | 0.006 [0.000, 0.018] | 0.000 [0.000, 0.000] | 0.006 [0.000, 0.018] | 0.000 | 0.994 |
| S0 | J5_cldr | 564 | 147 | 3 | 0 | 555 | 0 | 6 | 0.016 [0.003, 0.034] | 0.005 [0.000, 0.012] | 0.011 [0.000, 0.027] | 0.333 | 0.984 |
| S0 | J6_ambiguous | 9 | 9 | 0 | 5 | 0 | 0 | 4 | 0.444 [0.111, 0.778] | 0.556 [0.222, 0.889] | 0.444 [0.111, 0.778] | 0.000 | 0.000 |
| S0 | J7_region | 26 | 26 | 0 | 25 | 0 | 0 | 1 | 0.038 [0.000, 0.115] | 0.962 [0.885, 1.000] | 0.038 [0.000, 0.115] | 0.000 | 0.000 |
| S1 | **pooled** | 769 | 207 | 0 | 35 | 734 | 0 | 0 | 0.000 [0.000, 0.000] | 0.046 [0.030, 0.063] | 0.000 [0.000, 0.000] | – | 0.954 |
| S1 | J1_table | 81 | 27 | 81 | 0 | 0 | 0 | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.000 |
| S1 | J2_iso_code | 344 | 172 | 344 | 0 | 0 | 0 | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.000 |
| S1 | J3_iso_name | 271 | 168 | 271 | 0 | 0 | 0 | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.000 |
| S1 | J4_typo | 170 | 170 | 0 | 0 | 170 | 0 | 0 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | – | 1.000 |
| S1 | J5_cldr | 564 | 147 | 0 | 0 | 564 | 0 | 0 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | – | 1.000 |
| S1 | J6_ambiguous | 9 | 9 | 0 | 9 | 0 | 0 | 0 | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | – | 0.000 |
| S1 | J7_region | 26 | 26 | 0 | 26 | 0 | 0 | 0 | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | – | 0.000 |

#### A3. Tax-data behaviour: compute with the true jurisdiction's rates or refuse (pooled = J4–J7)

| System | Subset | n | Clusters | Correct | Safe abst. | Over-abst. | Expl. fail. | Silent err. | Coverage [95% cluster CI] | Decision acc. [CI] | Silent-error rate [CI] | Selective acc. | Over-abst. rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B | **pooled** | 769 | 207 | 0 | 0 | 0 | 0 | 769 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 | 0.000 |
| B | J1_table | 81 | 27 | 54 | 0 | 0 | 0 | 27 | 1.000 [1.000, 1.000] | 0.667 [0.667, 0.667] | 0.333 [0.333, 0.333] | 0.667 | 0.000 |
| B | J2_iso_code | 344 | 172 | 0 | 0 | 0 | 0 | 344 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 | 0.000 |
| B | J3_iso_name | 271 | 168 | 0 | 0 | 0 | 0 | 271 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 | 0.000 |
| B | J4_typo | 170 | 170 | 0 | 0 | 0 | 0 | 170 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 | 0.000 |
| B | J5_cldr | 564 | 147 | 0 | 0 | 0 | 0 | 564 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 | 0.000 |
| B | J6_ambiguous | 9 | 9 | 0 | 0 | 0 | 0 | 9 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 | 0.000 |
| B | J7_region | 26 | 26 | 0 | 0 | 0 | 0 | 26 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 | 0.000 |
| S0 | **pooled** | 769 | 207 | 3 | 0 | 0 | 0 | 766 | 1.000 [1.000, 1.000] | 0.004 [0.000, 0.009] | 0.996 [0.991, 1.000] | 0.004 | 0.000 |
| S0 | J1_table | 81 | 27 | 78 | 0 | 0 | 0 | 3 | 1.000 [1.000, 1.000] | 0.963 [0.926, 1.000] | 0.037 [0.000, 0.074] | 0.963 | 0.000 |
| S0 | J2_iso_code | 344 | 172 | 19 | 0 | 0 | 0 | 325 | 1.000 [1.000, 1.000] | 0.055 [0.026, 0.087] | 0.945 [0.913, 0.974] | 0.055 | 0.000 |
| S0 | J3_iso_name | 271 | 168 | 15 | 0 | 0 | 0 | 256 | 1.000 [1.000, 1.000] | 0.055 [0.030, 0.085] | 0.945 [0.915, 0.970] | 0.055 | 0.000 |
| S0 | J4_typo | 170 | 170 | 0 | 0 | 0 | 0 | 170 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 | 0.000 |
| S0 | J5_cldr | 564 | 147 | 3 | 0 | 0 | 0 | 561 | 1.000 [1.000, 1.000] | 0.005 [0.000, 0.012] | 0.995 [0.988, 1.000] | 0.005 | 0.000 |
| S0 | J6_ambiguous | 9 | 9 | 0 | 0 | 0 | 0 | 9 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 | 0.000 |
| S0 | J7_region | 26 | 26 | 0 | 0 | 0 | 0 | 26 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 | 0.000 |
| S1 | **pooled** | 769 | 207 | 0 | 632 | 137 | 0 | 0 | 0.000 [0.000, 0.000] | 0.822 [0.755, 0.883] | 0.000 [0.000, 0.000] | – | 0.178 |
| S1 | J1_table | 81 | 27 | 81 | 0 | 0 | 0 | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.000 |
| S1 | J2_iso_code | 344 | 172 | 54 | 290 | 0 | 0 | 0 | 0.157 [0.105, 0.215] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.000 |
| S1 | J3_iso_name | 271 | 168 | 24 | 247 | 0 | 0 | 0 | 0.089 [0.054, 0.127] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.000 |
| S1 | J4_typo | 170 | 170 | 0 | 143 | 27 | 0 | 0 | 0.000 [0.000, 0.000] | 0.841 [0.788, 0.894] | 0.000 [0.000, 0.000] | – | 0.159 |
| S1 | J5_cldr | 564 | 147 | 0 | 454 | 110 | 0 | 0 | 0.000 [0.000, 0.000] | 0.805 [0.728, 0.872] | 0.000 [0.000, 0.000] | – | 0.195 |
| S1 | J6_ambiguous | 9 | 9 | 0 | 9 | 0 | 0 | 0 | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | – | 0.000 |
| S1 | J7_region | 26 | 26 | 0 | 26 | 0 | 0 | 0 | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | – | 0.000 |

#### A4. Primary paired tests: 18 tests, cluster-level two-sided sign-flip permutation (10,000 permutations), Holm-adjusted over the 18 (** = Holm p < 0.05)

| Task | Metric | A → B | Items | Clusters | Rate A | Rate B | Diff (B−A) [95% cluster CI] | Permutation p | Holm p | McNemar discordant (A✗B✓ / A✓B✗) | McNemar p (item-level, secondary) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| product | decision_correct | B → S0 | 359 | 134 | 0.579 | 0.557 | -0.022 [-0.142, +0.071] | 0.707 | 1 | 84 / 92 | 0.598 |
| product | silent_error | B → S0 | 359 | 134 | 0.053 | 0.443 | +0.390 [+0.327, +0.470] | 0.0001 | 0.0018 ** | 140 / 0 | 1.43e-42 |
| product | decision_correct | S0 → S1 | 359 | 134 | 0.557 | 0.997 | +0.440 [+0.381, +0.513] | 0.0001 | 0.0018 ** | 158 / 0 | 5.47e-48 |
| product | silent_error | S0 → S1 | 359 | 134 | 0.443 | 0.000 | -0.443 [-0.515, -0.384] | 0.0001 | 0.0018 ** | 0 / 159 | 2.74e-48 |
| product | decision_correct | B → S1 | 359 | 134 | 0.579 | 0.997 | +0.418 [+0.365, +0.459] | 0.0001 | 0.0018 ** | 150 / 0 | 1.4e-45 |
| product | silent_error | B → S1 | 359 | 134 | 0.053 | 0.000 | -0.053 [-0.071, -0.034] | 0.0001 | 0.0018 ** | 0 / 19 | 3.81e-06 |
| identification | decision_correct | B → S0 | 769 | 207 | 0.046 | 0.043 | -0.003 [-0.010, +0.004] | 0.727 | 1 | 3 / 5 | 0.727 |
| identification | silent_error | B → S0 | 769 | 207 | 0.000 | 0.016 | +0.016 [+0.005, +0.029] | 0.00781 | 0.0703 | 12 / 0 | 0.000488 |
| identification | decision_correct | S0 → S1 | 769 | 207 | 0.043 | 0.046 | +0.003 [-0.004, +0.010] | 0.727 | 1 | 5 / 3 | 0.727 |
| identification | silent_error | S0 → S1 | 769 | 207 | 0.016 | 0.000 | -0.016 [-0.029, -0.005] | 0.00781 | 0.0703 | 0 / 12 | 0.000488 |
| identification | decision_correct | B → S1 | 769 | 207 | 0.046 | 0.046 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| identification | silent_error | B → S1 | 769 | 207 | 0.000 | 0.000 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| tax_behaviour | decision_correct | B → S0 | 769 | 207 | 0.000 | 0.004 | +0.004 [+0.000, +0.009] | 0.25 | 1 | 3 / 0 | 0.25 |
| tax_behaviour | silent_error | B → S0 | 769 | 207 | 1.000 | 0.996 | -0.004 [-0.009, +0.000] | 0.25 | 1 | 0 / 3 | 0.25 |
| tax_behaviour | decision_correct | S0 → S1 | 769 | 207 | 0.004 | 0.822 | +0.818 [+0.751, +0.880] | 0.0001 | 0.0018 ** | 632 / 3 | 5.99e-184 |
| tax_behaviour | silent_error | S0 → S1 | 769 | 207 | 0.996 | 0.000 | -0.996 [-1.000, -0.991] | 0.0001 | 0.0018 ** | 0 / 766 | 5.15e-231 |
| tax_behaviour | decision_correct | B → S1 | 769 | 207 | 0.000 | 0.822 | +0.822 [+0.757, +0.884] | 0.0001 | 0.0018 ** | 632 / 0 | 1.12e-190 |
| tax_behaviour | silent_error | B → S1 | 769 | 207 | 1.000 | 0.000 | -1.000 [-1.000, -1.000] | 0.0001 | 0.0018 ** | 0 / 769 | 6.44e-232 |

#### A5. Malformed inputs (18 items; not split and not held out: the same 18 were evaluated in the DEV stage)

| System | Rejected | Status counts | Landed costs computed for malformed input |
|---|---|---|---|
| B | 5/18 | ERROR 5, OK 13 | 13: -2985.4, -129.8, 129.8, 129.8, 1963.5, 1963.5, 2063.82, 2206.6, 2206.6, 2206.6, nan, nan, inf |
| S0 | 7/18 | ERROR 7, OK 11 | 11: -2985.4, -129.8, 129.8, 129.8, 2063.82, 2206.6, 2206.6, 2206.6, nan, nan, inf |
| S1 | 18/18 | INVALID 18 | 0: none |

#### A6. Error propagation into duty, VAT and landed cost (counts tabulated from the per-item `propagation` classification; no new computation)

| Scope | System | n | no error | masked flagged | masked silent | financial error flagged | financial error silent | computed when should refuse flagged | computed when should refuse silent | over refusal | explicit refusal | Rel. landed-cost error of financial errors: median / max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Product P1–P7 (country fixed) | B | 359 | 116 | 132 | 0 | 0 | 0 | 92 | 19 | 0 | 0 | – |
| Product P1–P7 (country fixed) | S0 | 359 | 200 | 0 | 48 | 0 | 0 | 0 | 111 | 0 | 0 | – |
| Product P1–P7 (country fixed) | S1 | 359 | 247 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 111 | – |
| Product P8 (country fixed) | B | 170 | 0 | 24 | 0 | 0 | 0 | 146 | 0 | 0 | 0 | – |
| Product P8 (country fixed) | S0 | 170 | 3 | 0 | 21 | 0 | 0 | 0 | 146 | 0 | 0 | – |
| Product P8 (country fixed) | S1 | 170 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 24 | 146 | – |
| Country J4–J7 (product fixed) | B | 769 | 0 | 0 | 0 | 0 | 137 | 0 | 632 | 0 | 0 | 0.1026 / 0.1375 (n=137) |
| Country J4–J7 (product fixed) | S0 | 769 | 3 | 0 | 0 | 0 | 134 | 0 | 632 | 0 | 0 | 0.1026 / 0.1375 (n=134) |
| Country J4–J7 (product fixed) | S1 | 769 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 137 | 632 | – |

Rates used for J4–J7 (per-item `tax_subtype`) and other per-item flags:

| System | Default rates (5 % duty / 10 % VAT) | Another country's rates | Correct rates | Refused | FX substituted | Fabricated HS (product P1–P7 / P8) | Wrong policy record (product P1–P7 / P8) |
|---|---|---|---|---|---|---|---|
| B | 769 | 0 | 0 | 0 | 0 | 0 / 0 | 0 / 0 |
| S0 | 754 | 12 | 3 | 0 | 1 | 120 / 88 | 14 / 11 |
| S1 | 0 | 0 | 0 | 769 | 0 | 0 / 0 | 0 / 0 |

### B. Secondary sensitivity analysis (pre-declared 24 Nov 2026): sibling clusters of the 8 excluded items also removed (18 product and 9 country items)


#### B1. Product, pooled P1–P7

| System | Subset | n | Clusters | Correct | Safe abst. | Over-abst. | Expl. fail. | Silent err. | Coverage [95% cluster CI] | Decision acc. [CI] | Silent-error rate [CI] | Selective acc. | Over-abst. rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B | **pooled** | 341 | 131 | 107 | 92 | 123 | 0 | 19 | 0.370 [0.324, 0.406] | 0.584 [0.541, 0.642] | 0.056 [0.037, 0.076] | 0.849 | 0.361 |
| S0 | **pooled** | 341 | 131 | 187 | 0 | 0 | 0 | 154 | 1.000 [1.000, 1.000] | 0.548 [0.473, 0.610] | 0.452 [0.390, 0.527] | 0.548 | 0.000 |
| S1 | **pooled** | 341 | 131 | 230 | 111 | 0 | 0 | 0 | 0.674 [0.588, 0.741] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.000 |

#### B2. Country identification, pooled J4–J7

| System | Subset | n | Clusters | Correct | Safe abst. | Over-abst. | Expl. fail. | Silent err. | Coverage [95% cluster CI] | Decision acc. [CI] | Silent-error rate [CI] | Selective acc. | Over-abst. rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B | **pooled** | 763 | 206 | 0 | 35 | 728 | 0 | 0 | 0.000 [0.000, 0.000] | 0.046 [0.031, 0.063] | 0.000 [0.000, 0.000] | – | 0.954 |
| S0 | **pooled** | 763 | 206 | 3 | 30 | 718 | 0 | 12 | 0.020 [0.008, 0.034] | 0.043 [0.029, 0.059] | 0.016 [0.005, 0.029] | 0.200 | 0.941 |
| S1 | **pooled** | 763 | 206 | 0 | 35 | 728 | 0 | 0 | 0.000 [0.000, 0.000] | 0.046 [0.031, 0.063] | 0.000 [0.000, 0.000] | – | 0.954 |

#### B3. Tax behaviour, pooled J4–J7

| System | Subset | n | Clusters | Correct | Safe abst. | Over-abst. | Expl. fail. | Silent err. | Coverage [95% cluster CI] | Decision acc. [CI] | Silent-error rate [CI] | Selective acc. | Over-abst. rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B | **pooled** | 763 | 206 | 0 | 0 | 0 | 0 | 763 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 | 0.000 |
| S0 | **pooled** | 763 | 206 | 3 | 0 | 0 | 0 | 760 | 1.000 [1.000, 1.000] | 0.004 [0.000, 0.009] | 0.996 [0.991, 1.000] | 0.004 | 0.000 |
| S1 | **pooled** | 763 | 206 | 0 | 626 | 137 | 0 | 0 | 0.000 [0.000, 0.000] | 0.820 [0.752, 0.880] | 0.000 [0.000, 0.000] | – | 0.180 |

#### B4. Paired tests with siblings removed (Holm over these 18)

| Task | Metric | A → B | Items | Clusters | Rate A | Rate B | Diff (B−A) [95% cluster CI] | Permutation p | Holm p | McNemar discordant (A✗B✓ / A✓B✗) | McNemar p (item-level, secondary) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| product | decision_correct | B → S0 | 341 | 131 | 0.584 | 0.548 | -0.035 [-0.161, +0.062] | 0.554 | 1 | 80 / 92 | 0.402 |
| product | silent_error | B → S0 | 341 | 131 | 0.056 | 0.452 | +0.396 [+0.332, +0.478] | 0.0001 | 0.0018 ** | 135 / 0 | 4.59e-41 |
| product | decision_correct | S0 → S1 | 341 | 131 | 0.548 | 1.000 | +0.452 [+0.390, +0.528] | 0.0001 | 0.0018 ** | 154 / 0 | 8.76e-47 |
| product | silent_error | S0 → S1 | 341 | 131 | 0.452 | 0.000 | -0.452 [-0.528, -0.390] | 0.0001 | 0.0018 ** | 0 / 154 | 8.76e-47 |
| product | decision_correct | B → S1 | 341 | 131 | 0.584 | 1.000 | +0.416 [+0.359, +0.461] | 0.0001 | 0.0018 ** | 142 / 0 | 3.59e-43 |
| product | silent_error | B → S1 | 341 | 131 | 0.056 | 0.000 | -0.056 [-0.075, -0.037] | 0.0001 | 0.0018 ** | 0 / 19 | 3.81e-06 |
| identification | decision_correct | B → S0 | 763 | 206 | 0.046 | 0.043 | -0.003 [-0.010, +0.004] | 0.727 | 1 | 3 / 5 | 0.727 |
| identification | silent_error | B → S0 | 763 | 206 | 0.000 | 0.016 | +0.016 [+0.005, +0.030] | 0.00781 | 0.0703 | 12 / 0 | 0.000488 |
| identification | decision_correct | S0 → S1 | 763 | 206 | 0.043 | 0.046 | +0.003 [-0.004, +0.010] | 0.727 | 1 | 5 / 3 | 0.727 |
| identification | silent_error | S0 → S1 | 763 | 206 | 0.016 | 0.000 | -0.016 [-0.030, -0.005] | 0.00781 | 0.0703 | 0 / 12 | 0.000488 |
| identification | decision_correct | B → S1 | 763 | 206 | 0.046 | 0.046 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| identification | silent_error | B → S1 | 763 | 206 | 0.000 | 0.000 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| tax_behaviour | decision_correct | B → S0 | 763 | 206 | 0.000 | 0.004 | +0.004 [+0.000, +0.009] | 0.25 | 1 | 3 / 0 | 0.25 |
| tax_behaviour | silent_error | B → S0 | 763 | 206 | 1.000 | 0.996 | -0.004 [-0.009, +0.000] | 0.25 | 1 | 0 / 3 | 0.25 |
| tax_behaviour | decision_correct | S0 → S1 | 763 | 206 | 0.004 | 0.820 | +0.817 [+0.751, +0.880] | 0.0001 | 0.0018 ** | 626 / 3 | 3.72e-182 |
| tax_behaviour | silent_error | S0 → S1 | 763 | 206 | 0.996 | 0.000 | -0.996 [-1.000, -0.991] | 0.0001 | 0.0018 ** | 0 / 760 | 3.3e-229 |
| tax_behaviour | decision_correct | B → S1 | 763 | 206 | 0.000 | 0.820 | +0.820 [+0.756, +0.881] | 0.0001 | 0.0018 ** | 626 / 0 | 7.18e-189 |
| tax_behaviour | silent_error | B → S1 | 763 | 206 | 1.000 | 0.000 | -1.000 [-1.000, -1.000] | 0.0001 | 0.0018 ** | 0 / 763 | 4.12e-230 |

### C. Exploratory analyses (separate family; not confirmatory)


#### C1. Attribution ladder and ablations: product, pooled P1–P7

| System | Subset | n | Clusters | Correct | Safe abst. | Over-abst. | Expl. fail. | Silent err. | Coverage [95% cluster CI] | Decision acc. [CI] | Silent-error rate [CI] | Selective acc. | Over-abst. rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L0_S0 | **pooled** | 359 | 134 | 200 | 0 | 0 | 0 | 159 | 1.000 [1.000, 1.000] | 0.557 [0.488, 0.618] | 0.443 [0.382, 0.512] | 0.557 | 0.000 |
| L1_+validation | **pooled** | 359 | 134 | 200 | 0 | 0 | 0 | 159 | 1.000 [1.000, 1.000] | 0.557 [0.488, 0.618] | 0.443 [0.382, 0.512] | 0.557 | 0.000 |
| L2_+iso_identification | **pooled** | 359 | 134 | 200 | 0 | 0 | 0 | 159 | 1.000 [1.000, 1.000] | 0.557 [0.488, 0.618] | 0.443 [0.382, 0.512] | 0.557 | 0.000 |
| L3_+tax_availability_refusal | **pooled** | 359 | 134 | 200 | 0 | 0 | 0 | 159 | 1.000 [1.000, 1.000] | 0.557 [0.488, 0.618] | 0.443 [0.382, 0.512] | 0.557 | 0.000 |
| L4_+product_abstention | **pooled** | 359 | 134 | 196 | 83 | 37 | 0 | 43 | 0.666 [0.590, 0.728] | 0.777 [0.740, 0.817] | 0.120 [0.084, 0.159] | 0.820 | 0.103 |
| L5_+s1_product_tiers(=S1) | **pooled** | 359 | 134 | 247 | 111 | 1 | 0 | 0 | 0.688 [0.607, 0.751] | 0.997 [0.991, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.003 |
| S0_-partial_country | **pooled** | 359 | 134 | 200 | 0 | 0 | 0 | 159 | 1.000 [1.000, 1.000] | 0.557 [0.488, 0.618] | 0.443 [0.382, 0.512] | 0.557 | 0.000 |
| S0_-token_overlap | **pooled** | 359 | 134 | 123 | 0 | 0 | 0 | 236 | 1.000 [1.000, 1.000] | 0.343 [0.296, 0.387] | 0.657 [0.613, 0.704] | 0.343 | 0.000 |
| S1_+country_typo | **pooled** | 359 | 134 | 247 | 111 | 1 | 0 | 0 | 0.688 [0.607, 0.751] | 0.997 [0.991, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 0.003 |
| S1_-coverage_guard | **pooled** | 359 | 134 | 247 | 110 | 1 | 0 | 1 | 0.691 [0.610, 0.752] | 0.994 [0.985, 1.000] | 0.003 [0.000, 0.010] | 0.996 | 0.003 |
| S1_-typo_tier | **pooled** | 359 | 134 | 163 | 111 | 85 | 0 | 0 | 0.454 [0.401, 0.495] | 0.763 [0.741, 0.792] | 0.000 [0.000, 0.000] | 1.000 | 0.237 |

#### C2. Attribution ladder and ablations: country identification, pooled J4–J7

| System | Subset | n | Clusters | Correct | Safe abst. | Over-abst. | Expl. fail. | Silent err. | Coverage [95% cluster CI] | Decision acc. [CI] | Silent-error rate [CI] | Selective acc. | Over-abst. rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L0_S0 | **pooled** | 769 | 207 | 3 | 30 | 724 | 0 | 12 | 0.020 [0.008, 0.034] | 0.043 [0.028, 0.059] | 0.016 [0.005, 0.029] | 0.200 | 0.941 |
| L1_+validation | **pooled** | 769 | 207 | 3 | 30 | 724 | 0 | 12 | 0.020 [0.008, 0.034] | 0.043 [0.028, 0.059] | 0.016 [0.005, 0.029] | 0.200 | 0.941 |
| L2_+iso_identification | **pooled** | 769 | 207 | 0 | 35 | 734 | 0 | 0 | 0.000 [0.000, 0.000] | 0.046 [0.030, 0.063] | 0.000 [0.000, 0.000] | – | 0.954 |
| L3_+tax_availability_refusal | **pooled** | 769 | 207 | 0 | 35 | 734 | 0 | 0 | 0.000 [0.000, 0.000] | 0.046 [0.030, 0.063] | 0.000 [0.000, 0.000] | – | 0.954 |
| L4_+product_abstention | **pooled** | 769 | 207 | 0 | 35 | 734 | 0 | 0 | 0.000 [0.000, 0.000] | 0.046 [0.030, 0.063] | 0.000 [0.000, 0.000] | – | 0.954 |
| L5_+s1_product_tiers(=S1) | **pooled** | 769 | 207 | 0 | 35 | 734 | 0 | 0 | 0.000 [0.000, 0.000] | 0.046 [0.030, 0.063] | 0.000 [0.000, 0.000] | – | 0.954 |
| S0_-partial_country | **pooled** | 769 | 207 | 0 | 35 | 734 | 0 | 0 | 0.000 [0.000, 0.000] | 0.046 [0.030, 0.063] | 0.000 [0.000, 0.000] | – | 0.954 |
| S0_-token_overlap | **pooled** | 769 | 207 | 3 | 30 | 724 | 0 | 12 | 0.020 [0.008, 0.034] | 0.043 [0.028, 0.059] | 0.016 [0.005, 0.029] | 0.200 | 0.941 |
| S1_+country_typo | **pooled** | 769 | 207 | 270 | 35 | 464 | 0 | 0 | 0.351 [0.314, 0.394] | 0.397 [0.357, 0.444] | 0.000 [0.000, 0.000] | 1.000 | 0.603 |
| S1_-coverage_guard | **pooled** | 769 | 207 | 0 | 35 | 734 | 0 | 0 | 0.000 [0.000, 0.000] | 0.046 [0.030, 0.063] | 0.000 [0.000, 0.000] | – | 0.954 |
| S1_-typo_tier | **pooled** | 769 | 207 | 0 | 35 | 734 | 0 | 0 | 0.000 [0.000, 0.000] | 0.046 [0.030, 0.063] | 0.000 [0.000, 0.000] | – | 0.954 |

#### C3. Attribution ladder and ablations: tax behaviour, pooled J4–J7

| System | Subset | n | Clusters | Correct | Safe abst. | Over-abst. | Expl. fail. | Silent err. | Coverage [95% cluster CI] | Decision acc. [CI] | Silent-error rate [CI] | Selective acc. | Over-abst. rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L0_S0 | **pooled** | 769 | 207 | 3 | 0 | 0 | 0 | 766 | 1.000 [1.000, 1.000] | 0.004 [0.000, 0.009] | 0.996 [0.991, 1.000] | 0.004 | 0.000 |
| L1_+validation | **pooled** | 769 | 207 | 3 | 0 | 0 | 0 | 766 | 1.000 [1.000, 1.000] | 0.004 [0.000, 0.009] | 0.996 [0.991, 1.000] | 0.004 | 0.000 |
| L2_+iso_identification | **pooled** | 769 | 207 | 0 | 0 | 0 | 0 | 769 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 | 0.000 |
| L3_+tax_availability_refusal | **pooled** | 769 | 207 | 0 | 632 | 137 | 0 | 0 | 0.000 [0.000, 0.000] | 0.822 [0.755, 0.883] | 0.000 [0.000, 0.000] | – | 0.178 |
| L4_+product_abstention | **pooled** | 769 | 207 | 0 | 632 | 137 | 0 | 0 | 0.000 [0.000, 0.000] | 0.822 [0.755, 0.883] | 0.000 [0.000, 0.000] | – | 0.178 |
| L5_+s1_product_tiers(=S1) | **pooled** | 769 | 207 | 0 | 632 | 137 | 0 | 0 | 0.000 [0.000, 0.000] | 0.822 [0.755, 0.883] | 0.000 [0.000, 0.000] | – | 0.178 |
| S0_-partial_country | **pooled** | 769 | 207 | 0 | 0 | 0 | 0 | 769 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 | 0.000 |
| S0_-token_overlap | **pooled** | 769 | 207 | 3 | 0 | 0 | 0 | 766 | 1.000 [1.000, 1.000] | 0.004 [0.000, 0.009] | 0.996 [0.991, 1.000] | 0.004 | 0.000 |
| S1_+country_typo | **pooled** | 769 | 207 | 43 | 632 | 94 | 0 | 0 | 0.056 [0.035, 0.079] | 0.878 [0.826, 0.923] | 0.000 [0.000, 0.000] | 1.000 | 0.122 |
| S1_-coverage_guard | **pooled** | 769 | 207 | 0 | 632 | 137 | 0 | 0 | 0.000 [0.000, 0.000] | 0.822 [0.755, 0.883] | 0.000 [0.000, 0.000] | – | 0.178 |
| S1_-typo_tier | **pooled** | 769 | 207 | 0 | 632 | 137 | 0 | 0 | 0.000 [0.000, 0.000] | 0.822 [0.755, 0.883] | 0.000 [0.000, 0.000] | – | 0.178 |

#### C4. Ladder step tests: 30 tests, Holm-adjusted within the exploratory family

| Task | Metric | A → B | Items | Clusters | Rate A | Rate B | Diff (B−A) [95% cluster CI] | Permutation p | Holm p | McNemar discordant (A✗B✓ / A✓B✗) | McNemar p (item-level, secondary) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| product | decision_correct | L0_S0 → L1_+validation | 359 | 134 | 0.557 | 0.557 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| product | silent_error | L0_S0 → L1_+validation | 359 | 134 | 0.443 | 0.443 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| product | decision_correct | L1_+validation → L2_+iso_identification | 359 | 134 | 0.557 | 0.557 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| product | silent_error | L1_+validation → L2_+iso_identification | 359 | 134 | 0.443 | 0.443 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| product | decision_correct | L2_+iso_identification → L3_+tax_availability_refusal | 359 | 134 | 0.557 | 0.557 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| product | silent_error | L2_+iso_identification → L3_+tax_availability_refusal | 359 | 134 | 0.443 | 0.443 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| product | decision_correct | L3_+tax_availability_refusal → L4_+product_abstention | 359 | 134 | 0.557 | 0.777 | +0.220 [+0.159, +0.299] | 0.0001 | 0.003 ** | 83 / 4 | 3.02e-20 |
| product | silent_error | L3_+tax_availability_refusal → L4_+product_abstention | 359 | 134 | 0.443 | 0.120 | -0.323 [-0.402, -0.260] | 0.0001 | 0.003 ** | 0 / 116 | 2.41e-35 |
| product | decision_correct | L4_+product_abstention → L5_+s1_product_tiers(=S1) | 359 | 134 | 0.777 | 0.997 | +0.220 [+0.183, +0.256] | 0.0001 | 0.003 ** | 79 / 0 | 3.31e-24 |
| product | silent_error | L4_+product_abstention → L5_+s1_product_tiers(=S1) | 359 | 134 | 0.120 | 0.000 | -0.120 [-0.158, -0.082] | 0.0001 | 0.003 ** | 0 / 43 | 2.27e-13 |
| identification | decision_correct | L0_S0 → L1_+validation | 769 | 207 | 0.043 | 0.043 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| identification | silent_error | L0_S0 → L1_+validation | 769 | 207 | 0.016 | 0.016 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| identification | decision_correct | L1_+validation → L2_+iso_identification | 769 | 207 | 0.043 | 0.046 | +0.003 [-0.004, +0.010] | 0.727 | 1 | 5 / 3 | 0.727 |
| identification | silent_error | L1_+validation → L2_+iso_identification | 769 | 207 | 0.016 | 0.000 | -0.016 [-0.029, -0.005] | 0.00781 | 0.188 | 0 / 12 | 0.000488 |
| identification | decision_correct | L2_+iso_identification → L3_+tax_availability_refusal | 769 | 207 | 0.046 | 0.046 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| identification | silent_error | L2_+iso_identification → L3_+tax_availability_refusal | 769 | 207 | 0.000 | 0.000 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| identification | decision_correct | L3_+tax_availability_refusal → L4_+product_abstention | 769 | 207 | 0.046 | 0.046 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| identification | silent_error | L3_+tax_availability_refusal → L4_+product_abstention | 769 | 207 | 0.000 | 0.000 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| identification | decision_correct | L4_+product_abstention → L5_+s1_product_tiers(=S1) | 769 | 207 | 0.046 | 0.046 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| identification | silent_error | L4_+product_abstention → L5_+s1_product_tiers(=S1) | 769 | 207 | 0.000 | 0.000 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| tax_behaviour | decision_correct | L0_S0 → L1_+validation | 769 | 207 | 0.004 | 0.004 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| tax_behaviour | silent_error | L0_S0 → L1_+validation | 769 | 207 | 0.996 | 0.996 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| tax_behaviour | decision_correct | L1_+validation → L2_+iso_identification | 769 | 207 | 0.004 | 0.000 | -0.004 [-0.009, +0.000] | 0.25 | 1 | 0 / 3 | 0.25 |
| tax_behaviour | silent_error | L1_+validation → L2_+iso_identification | 769 | 207 | 0.996 | 1.000 | +0.004 [+0.000, +0.009] | 0.25 | 1 | 3 / 0 | 0.25 |
| tax_behaviour | decision_correct | L2_+iso_identification → L3_+tax_availability_refusal | 769 | 207 | 0.000 | 0.822 | +0.822 [+0.757, +0.884] | 0.0001 | 0.003 ** | 632 / 0 | 1.12e-190 |
| tax_behaviour | silent_error | L2_+iso_identification → L3_+tax_availability_refusal | 769 | 207 | 1.000 | 0.000 | -1.000 [-1.000, -1.000] | 0.0001 | 0.003 ** | 0 / 769 | 6.44e-232 |
| tax_behaviour | decision_correct | L3_+tax_availability_refusal → L4_+product_abstention | 769 | 207 | 0.822 | 0.822 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| tax_behaviour | silent_error | L3_+tax_availability_refusal → L4_+product_abstention | 769 | 207 | 0.000 | 0.000 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| tax_behaviour | decision_correct | L4_+product_abstention → L5_+s1_product_tiers(=S1) | 769 | 207 | 0.822 | 0.822 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |
| tax_behaviour | silent_error | L4_+product_abstention → L5_+s1_product_tiers(=S1) | 769 | 207 | 0.000 | 0.000 | +0.000 [+0.000, +0.000] | 1 | 1 | 0 / 0 | 1 |

### D. The 8 pilot TEST items excluded from every metric (`primary_test_excluded_from_metrics.csv`)

| Pilot ID | Benchmark | Item ID | Category | Cluster |
|---|---|---|---|---|
| P01 | product | `P2_format|Scanner|ws_punct` | P2_format | `base:Scanner` |
| P02 | product | `P3_typo|Graphics Card|typo|0` | P3_typo | `base:Graphics Card` |
| P03 | product | `P4_short|WiFi Adapter|head_noun` | P4_short | `base:WiFi Adapter` |
| P05 | product | `P6_ambiguous|word|computer` | P6_ambiguous | `P6_ambiguous|word|computer` |
| P06 | product | `P7_outside|card index` | P7_outside | `P7_outside|card index` |
| P07 | product | `P8_hs|other_chapter|080122` | P8_hs_formal | `P8_hs|other_chapter|080122` |
| P09 | country | `CB|DZ|official_name` | J3_iso_name | `DZ` |
| P10 | country | `CE|sint` | J6_ambiguous | `CE|sint` |

### C (summary). Exploratory observations (one change per ladder step; not confirmatory)

- Product gains appear at two steps:
  - L4, product abstention: silent-error rate 0.443 → 0.120, decision accuracy 0.557 → 0.777;
  - L5, S1's evidence tiers: silent-error rate → 0.000, decision accuracy → 0.997.

  L1–L3 leave product results unchanged.
- The tax-behaviour gain comes entirely from L3, refusal without tax data (decision accuracy 0.000 → 0.822,
  silent-error rate 1.000 → 0.000).
- L2, ISO identification, removes S0's 12 identification silent errors, but the step is not significant within
  the exploratory family (Holm p = 0.1875).
- Ablations:
  - Without its typo tier, S1's product coverage falls to 0.454 (decision accuracy 0.763).
  - Without the coverage guard, S1 makes 1 silent error on P1–P7 and 13 on P8.
  - Adding country-typo matching raises identification decision accuracy on J4–J7 to 0.397 with no silent
    errors, and tax decision accuracy to 0.878. This variant was not the pre-declared S1 and is not a result
    for S1.
  - Removing S0's token-overlap tier raises its product silent-error rate to 0.657.

## 7. Output files (under `research_paper/experiments/results/`, committed unedited in `e0bf964`)

All run files are in `runs/20261127T104925Z-0f293784/`.

| Path (relative to that folder) | Content |
|---|---|
| `run.json` | Authorisation, hashes verified at open, git state, tuning choice, environment, code file hashes |
| `close.json` | Status `completed`, finish time, binding hash of the output inventory |
| `outputs_sha256.json` | SHA-256 of all 30 run outputs |
| `raw/primary_test_outputs.jsonl`, `raw/ladder_test_outputs.jsonl` | Raw system outputs for every scored item and system |
| `processed/primary_test_{product,identification,tax_behaviour}_summary.csv` | Primary metrics with cluster-bootstrap and Wilson intervals |
| `processed/primary_test_paired_tests.csv` | The 18 primary paired tests (permutation p, Holm p, McNemar) |
| `processed/primary_test_{product,country,malformed}_items.csv` | Per-item outcomes, propagation class, rates used, flags |
| `processed/primary_test_excluded_from_metrics.csv` | The 8 excluded pilot items with reasons (audit) |
| `processed/primary_test_provenance.json`, `primary_test_sensitivity_siblings_info.json` | Provenance; sensitivity definition |
| `processed/primary_sensitivity_siblings_removed_test_*` | Secondary sensitivity summaries and paired tests |
| `processed/ladder_test_*` | Exploratory ladder and ablation outputs (separate family) |
| `figures/primary_test_{product,identification,tax_behaviour}_summary_outcomes.pdf` | Outcome-composition figures (see known issue in §1) |
| `figures/figures_provenance.json` | Figure inputs with SHA-256 |

Also in `results/`: `test_runs.jsonl` (append-only run log), `test_stage_record.json` (command, times, SHA-256 of
every TEST file) and `test_stage_logs/stage_evaluate_test_console.txt`.

## 8. Limitations

- **Synthetic data.** The catalogue (60 types, 43 HS-6 codes), the perturbations and the unsourced tax rates
  (40 jurisdictions) are synthetic, so financial correctness is relative to the project's own table.
- **Not legal advice.** HS texts come from an unofficial mirror (not WCO legal text). No result establishes legal
  or official classification validity or real-world customs compliance.
- **Product errors and cost.** Duty and VAT in the original tables depend only on the country, so product errors
  cannot change costs. The absence of financial error in the product task is a property of this application, not
  evidence that product errors are harmless.
- **S1's identification table.** S1 covers only ISO names and codes, and all held-out country forms defeat it. Its
  safety on J4–J7 comes from abstention and refusal.
- **Same team.** The same team, with AI assistance, designed the systems and the benchmark; labels are
  independent of system outputs, but this remains a threat to validity.
- **Small categories.** P4, P5, P6, J6 and J7 have few clusters and are descriptive only.
- **Single run.** One TEST run was made, as planned. It will not be repeated to change results.
