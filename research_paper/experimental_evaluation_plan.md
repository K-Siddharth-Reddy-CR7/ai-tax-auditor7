# Experimental Evaluation Plan (Phase 3 — proposed, awaiting author approval)

All experiments below are **planned, not executed**. No numbers in this file are results.

## 0. Principles
1. **Label independence.** Every label comes from an external reference, from the perturbation generator, or from human annotators who never see system output. No system's prediction is ever used as a label.
2. **Freeze before run.** Benchmark files are generated, reviewed, frozen and SHA-256 hashed *before* any system is run on them. The hashes are recorded in `experiments/data/MANIFEST.json`.
3. **Single tuned parameter, tuned on dev only.** S1 has exactly one tuned parameter, the product abstention threshold τ. All headline metrics are computed on the **test** split.
4. **Same tables, same arithmetic.** B, S0 and S1 share `products`, `taxes`, `trade_policies` and the landed-cost formula. Any output difference is therefore caused by resolution or validation logic.
5. **Determinism.** Global seed 20261114 is used for all sampling and perturbation. Systems are deterministic, so reruns must reproduce results bit-for-bit (checked automatically).

## 1. Benchmarks

### 1.1 Product resolution benchmark (PRB)
The label is a catalogue **base type** (60 types) and its **HS-6** code, or **ABSTAIN** for goods the catalogue does not cover. Correctness is judged at the HS-6 level, because several base types share one code (e.g. Router, Modem, Network Switch, WiFi Adapter and Smartwatch → 851762).

| Subset | Source | Size (planned) | Label provenance |
|---|---|---|---|
| P1 Catalogue variants | Base-type names under seeded perturbations: (a) variant suffix stripped, (b) case/whitespace/punctuation noise, (c) one random edit (insert/delete/substitute/transpose) on a token ≥4 chars, (d) token reorder (multi-token names), (e) simple plural | 60 types × 5 = 300 (minus duplicates) | By construction (generator knows the source type) |
| P2 Official in-domain text | HS 2022 subheading descriptions of the **43** catalogue codes | 43 | HS nomenclature (external) |
| P3 Near-domain unsupported | HS 2022 descriptions of subheadings in chapters 84/85/94/95 **not** in the catalogue | random sample 120 | HS nomenclature → ABSTAIN |
| P4 Far out-of-domain | HS 2022 descriptions from all other chapters | random sample 120 | HS nomenclature → ABSTAIN |
| P5 Human-written | Invoice-style descriptions written by authors: 2 per base type, plus 40 unsupported goods | 160 | Writer label + blind second annotator; adjudicated (see `annotation_guidelines.md`) |

**HS source:** `datasets/harmonized-system` v2022.0 (UN Comtrade-derived, ODC-PDDL). File SHA-256 `e77ee9e1cfd15a42d1fadeb2c0618d10f6b9ed9aec0e5d66826dc7ef9d3126a5`, retrieved 2026-11-14. These descriptions are UN Comtrade's abridged texts, not the WCO legal text. All 43 catalogue codes were verified to exist in this edition.

**Splits.**
- P1 and P5 are split by base type (group split, 40 % dev / 60 % test, seeded), so that perturbations of one type never straddle splits.
- P2–P4 are split randomly (40/60), stratified by subset.
- Dev is used **only** to choose τ.

### 1.2 Jurisdiction resolution benchmark (JRB)
The label is one of the 40 supported jurisdictions, **UNSUPPORTED** (a real country not in the tax table), or **ABSTAIN** (ambiguous or non-country string).

| Subset | Source | Size | Label provenance |
|---|---|---|---|
| J1 Canonical | Table names + case/whitespace noise | 80 | Table |
| J2 ISO forms | ISO 3166-1 alpha-2, alpha-3, `name`, `official_name`, `common_name` for the 40 countries (pycountry 26.2.16) | ~170 (deduplicated) | ISO 3166-1 |
| J3 Typos | One seeded edit on canonical names | 40 | By construction |
| J4 Unsupported real countries | **All** ISO 3166-1 countries not in the table (population, not a sample) | 209 | ISO 3166-1 → UNSUPPORTED |
| J5 Colloquial / ambiguous (held out) | Author-written colloquial names (e.g. "Holland", "Britain") and ambiguous strings (e.g. "Korea", "Congo", "Guinea") | ~60 | Human, double-annotated |

**Leakage note.** S1's alias table is built from ISO 3166-1, so S1 is expected to solve J2 *by design*. J2 results are reported separately and are not presented as generalisation. J5 is excluded from the alias table and tests behaviour beyond it.

### 1.3 End-to-end transaction benchmark (E2E)
- Each of the 400 synthetic transactions keeps its numeric fields (unit price, quantity, freight).
- Its product and destination strings are replaced by items drawn (seeded, with replacement) from the **test** splits of PRB and JRB.
- Expected output = (HS-6, duty %, VAT %, landed cost) computed from the true labels and the project's own tables, or ABSTAIN if either label is ABSTAIN/UNSUPPORTED.
- Three draws give 1,200 transactions.

## 2. Outcome taxonomy (per item)
| Outcome | Definition |
|---|---|
| **Correct** | Answered, and the answer equals the label |
| **Safe abstention** | Abstained, and the label is ABSTAIN/UNSUPPORTED |
| **Over-abstention** | Abstained, but the label is a supported class |
| **Silent error** | Answered with a wrong value *without* any warning. This includes fabricated defaults: S0's 8471.30 fallback and the 5 %/10 % default rates |
| **Masked error** (E2E only) | Wrong HS-6 but correct landed cost |

## 3. Metrics
- **Coverage** = answered / all.
- **Accuracy** = correct / all. **Selective accuracy** = correct / answered.
- **Silent-error rate (SER)** = silent errors / all. This is the primary safety metric.
- **False-acceptance rate** on unsupported subsets (P3, P4, P5-unsupported, J4, J5-ambiguous).
- **Risk–coverage curve and AURC** for S1 (sweeping τ). B and S0 appear as single operating points.
- **E2E:**
  - share Correct / Safe / Silent-wrong-cost / Masked;
  - relative landed-cost error |L̂−L*|/L* on silent-wrong-cost items (median, max);
  - stage attribution (product vs. jurisdiction vs. both).
- **Per-subset breakdown** for every metric. **Error categories:** wrong HS same chapter, wrong chapter, fabricated fallback, wrong real country, default rates applied.
- **Latency:** per transaction (mean ± SD, median, p95, p99) and throughput (tx/s).

Confusion matrices: a 43-class HS matrix is not readable in print. The paper will show an error-category table, and the full confusion matrices will be released as CSV.

## 4. Statistics
- 95 % **Wilson score intervals** for all proportions.
- **Paired exact McNemar tests** (B vs S0, S0 vs S1, B vs S1) on per-item Correct and Silent-error indicators, on the same test items. **Holm–Bonferroni** correction across the family of comparisons. Effect sizes are reported as differences in proportions with 95 % CIs.
- Annotation reliability: **Cohen's κ** between the two annotators (P5, J5), with raw agreement.
- Latency: medians with bootstrap 95 % CI (10,000 resamples, seeded).
- No significance claim will be made beyond these tests.

## 5. Ablation (one variable at a time, all on the test split)
| Variant | Change relative to parent |
|---|---|
| S0 − token-overlap tier | Remove tier 3 of `product_agent` |
| S0 − HS fallback | Unknown product → abstain instead of 8471.30 |
| S0 − partial country match | Remove bidirectional substring match in `tax_agent` |
| S1 − abstention | τ = 0 (always return the best match) |
| S1 − ISO alias table | Exact canonical names only |
| S1 + fuzzy country | Add char-trigram fuzzy country match (threshold tuned on J-dev) |
| S1 − input validation | Accept raw inputs as S0 does (on malformed-input set M) |

Malformed-input set **M** (30 items): whitespace-only names, negative/zero price, quantity 0, non-integer quantity, NaN/inf, missing fields. Expected outcome: rejected with a reason.

## 6. Computational performance
- In-process timing with `time.perf_counter_ns`: warm-up of 200 calls, then 30 repetitions over the 1,200 E2E transactions per system.
- Optional HTTP measurement through the Flask app on loopback.
- CPU pinned with `taskset` where available.
- Recorded environment: CPU model, cores, RAM, OS, Python and library versions.
- Results are reported as indicative for a shared cloud VM, not as production benchmarks.

## 7. Threats to validity (to be carried into the paper)
- P1/J3 perturbations are synthetic and may not reflect real declaration noise. P5/J5 mitigate this, but they are small and author-written.
- P2–P4 use abridged HS texts, whose formal style differs from invoice text.
- The catalogue covers 60 base types in four HS chapters. Results do not generalise to full HS classification.
- Tax rates are unsourced prototype values, so financial errors are relative to the project's tables, not to law.
- Author-written items risk being unconsciously tailored. Mitigations: written before any S1 code is shown to annotators, frozen and hashed before evaluation, and quota-driven.
- Choosing τ on dev from the same distribution may overstate S1's test performance on other distributions.
- The authors developed both the systems and the benchmark.

## 8. Reproducibility
One command, `python research_paper/experiments/run_all.py`, regenerates benchmarks (if absent), runs all systems, ablations and statistics, and writes `results/raw/*.jsonl`, `results/processed/*.csv`, figures and a `results/REPORT.md`. Every number in the manuscript must be traceable to a row in `results/processed/`.
