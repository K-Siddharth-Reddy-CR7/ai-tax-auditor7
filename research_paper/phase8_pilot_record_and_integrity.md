# Phase 8 — Pilot Record and Held-Out Integrity (23 Nov 2026)

**Status:**
- Pilot review completed.
- Look-alike review in progress: batch 1 of 4 shown, no decisions yet.
- **Not frozen. No tuning or evaluation. No manuscript.**

## 1. Pilot record
| Item | Input | Split | Decision |
|---|---|---|---|
| P01 | `Scanner ` | test | Accept |
| P02 | `Graphics Chrd` | test | Accept |
| P03 | `Adapter` | test | Accept |
| P04 | `Memoury Card` | **dev** | Accept |
| P05 | `Computer` | test | Accept |
| P06 | `card index` | test | Accept |
| P07 | `Nuts, edible; brazil nuts, fresh or dried, shelled` | test | Accept |
| P08 | `Nueva Zelanda` | **dev** | Accept |
| P09 | `People's Democratic Republic of Algeria` | test | Accept |
| P10 | `Sint` | test | Accept |

- **Reviewer:** Author 1 (Syeda Sayeeda Farhath), sole reviewer.
- **Comments:** none. **Time spent:** not reported.
- **How recorded:** reported on 23 Nov 2026 and transcribed by the AI assistant into `experiments/pilot/pilot_review_sheet_v4.csv`. Machine-readable record: `experiments/pilot/pilot_reviewed_items.json`.
- **Outcome under the pre-declared rule:** 10/10 Accept, so the labelling rules are accepted, with no rule changes and no replacement items. No inter-annotator agreement is claimed.

## 2. Held-out integrity: findings
- **Inspected test items:** 8 of the 10 pilot items are in TEST. Their text and gold labels have now been seen by a human. No system output was ever shown, and no system has been run on any TEST benchmark item.
- **Dev items:** P04 and P08 are in DEV, which is used only for tuning. A human-checked label there does not threaten held-out integrity, so no change is needed.
- **Cluster siblings:** six of the inspected TEST items share a cluster with other TEST items (e.g. the other 5 "Scanner" strings, and 9 other strings for DZ). The siblings are *different strings*, their labels follow from the same rule the reviewer accepted, and the reviewer saw no performance information. They do not need exclusion. A sensitivity check is still recommended below.

## 3. Options considered
| Option | What changes | Verdict |
|---|---|---|
| **A. Evaluation-time exclusion list** | Labels and splits unchanged. The final TEST metrics drop the 8 item IDs in `pilot_reviewed_items.json`. The 10 pilot items are reported separately as an "inspected" set | **Recommended**: least disruptive, explicit, reproducible |
| B. Move the 8 items to DEV | Changes the split of 8 items, and breaks the group-level split: e.g. the Scanner and DZ clusters would straddle DEV/TEST, which is the leakage the design prevents | Not recommended |
| C. Re-draw splits or rebuild with a new seed | Changes every split assignment after labels were inspected | Not recommended |
| D. Do nothing | Final TEST would contain 8 inspected items without disclosure | Not acceptable |

## 4. Exact changes required to implement Option A
These are **proposed, not yet implemented**. They are to be done before freezing, with your approval.
1. `lexeval/evaluate.py`:
   - in `load(split="test")`, read `pilot/pilot_reviewed_items.json` and remove those `item_id`s from the TEST lists;
   - write them to separate `*_inspected_items.csv` rows (descriptive only, never pooled).

   About 10 lines plus one unit test. Labels, splits and benchmark files are unchanged.
2. `run_all.py --stage freeze`: add the SHA-256 of `pilot_reviewed_items.json` to `MANIFEST.json`, so the exclusion list is fixed with the data.
3. **Sensitivity analysis (secondary, reported in the paper):** re-compute the main TEST metrics after also removing the clusters of the inspected items:
   - base types: Scanner, Graphics Card, WiFi Adapter;
   - country: DZ;
   - singletons: the 'computer', 'card index', '080122' and 'sint' items.

   This shows the conclusions do not depend on them.
4. **Paper disclosure:** "Ten benchmark items were inspected during a labelling-rule pilot; the eight in the test split are excluded from all reported test metrics."

TEST sizes after exclusion:

| Category | Before | After |
|---|---|---|
| P2 | 76 | 75 |
| P3 | 76 | 75 |
| P4 | 16 | 15 |
| P6 | 11 | 10 |
| P7 | 89 | 88 |
| P8 | 171 | 170 |
| J3 | 272 | 271 |
| J6 | 10 | 9 |

All other categories are unchanged. Tuning rules, labels and splits are untouched.

## 5. Look-alike review: why it is not treated the same way
- The 16-item P7 look-alike review is **label construction applied uniformly to every item in that subgroup**, in both splits. It is not a probe of a sample, and its decisions determine the gold set itself.
- Excluding those items from TEST would remove the subgroup entirely. They stay in their splits, and the paper states that this subgroup's labels were human-confirmed.
- "card index" (look-alike #2) is also pilot item P06, so Option A excludes it from TEST regardless.
