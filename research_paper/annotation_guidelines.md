# Annotation Guidelines (draft v0.1 — for author review)

Two small human-written subsets make the benchmark less synthetic:
- **P5** — product descriptions;
- **J5** — colloquial and ambiguous country strings.

Everything else is labelled automatically from external references (HS 2022, ISO 3166-1) or by construction.

## Roles
| Role | Person (proposed) | Task |
|---|---|---|
| Writer (W) | Author 2 (Siddharth Karanam) | Writes items and assigns an intended label |
| Annotator (A) | Author 3 (P. Naga Bhargav Reddy) | Labels the same items **blind** to W's label |
| Adjudicator (J) | Author 1 (Syeda Sayeeda Farhath); Author 4 (Baalne Anjali) for unresolved cases | Resolves disagreements and records the reason |

The role assignment is a proposal; the authors may swap roles.

**Rules for everyone:**
- Do not run LEXITAX AUDIT (any version) on your items.
- Do not look at S1 code before items are frozen.
- Do not use AI tools to write or label items.

## What counts as one item
- **P5 item:** a single product description string of **3–15 words**, written the way it might appear on a commercial invoice or packing list. The intended label is either one of the 60 catalogue base types, or `UNSUPPORTED`.
- **J5 item:** a single destination string of **1–5 words**. The intended label is one of the 40 table countries, `UNSUPPORTED` (a real country not in the table), or `AMBIGUOUS` (could reasonably mean more than one country, or is not a country).

## Labels
- **Base type** (P5): choose from `labels/base_types.csv` (60 rows: name, HS-6, short HS description). Label the *thing*, not the brand. If the description fits two base types that share one HS-6 code (e.g. "camera" → Digital/Video Camera, both 852589), label `MULTI:<hs6>`. It is scored at HS level.
- **UNSUPPORTED** (P5): goods clearly outside all 60 types (e.g. "cotton t-shirts", "frozen shrimp", "car tyres").
- **AMBIGUOUS** (P5): the text cannot be resolved even by a human (e.g. "electronic device", "spare parts"). Scored as should-abstain.
- **J5 labels:** the country, `UNSUPPORTED` or `AMBIGUOUS`.

## Writing quotas (W)
| Subset | Quota |
|---|---|
| P5 in-catalogue | 2 per base type = 120. Item 1 is a plain synonym or paraphrase (e.g. "notebook computer 14 inch"). Item 2 adds invoice-style detail (model-like codes, quantities, materials), e.g. "Li-ion power bank 20000mAh black". Do not copy the catalogue name verbatim. |
| P5 unsupported | 40, spread over at least 10 HS chapters, including 10 "look-alike" goods (e.g. "car battery charger cable", "toy laptop for kids", "laptop bag"). |
| P5 ambiguous | 10 |
| J5 | 1–2 colloquial or native-language names for countries where one exists (e.g. "Holland", "Deutschland", "Britain", "Emirates"), ~35 items; plus ~15 ambiguous/non-country strings (e.g. "Korea", "Congo", "Guinea", "EU", "Europe"); plus ~10 sub-national or territory names (e.g. "Northern Ireland", "Hong Kong", "Scotland"), labelled as their ISO-correct outcome. |

## Positive and negative examples
| Text | Correct label | Why |
|---|---|---|
| "notebook PC, 15.6in, 8GB RAM" | Laptop (847130) | Paraphrase of laptop |
| "laptop sleeve neoprene" | UNSUPPORTED | Bag/case, not a laptop |
| "USB-C wall charger 65W" | Battery Charger (850440) | Charger |
| "wireless earbuds with charging case" | Wireless Headphones (851830) | |
| "drone with 4K camera" | UNSUPPORTED | Not a catalogue type |
| "spare parts" | AMBIGUOUS | Unresolvable |
| "Holland" (J5) | Netherlands | Colloquial |
| "Korea" (J5) | AMBIGUOUS | North or South |
| "Hong Kong" (J5) | UNSUPPORTED | ISO territory not in table |

## Procedure
1. W writes all items in `annotation/P5_writer.csv` and `annotation/J5_writer.csv`, with columns: `item_id, text, writer_label, writer_note`.
2. A script strips `writer_label` and shuffles the items into `annotation/P5_blind.csv`.
3. A labels the blind file, with columns: `item_id, annotator_label, confidence(1-3), note`.
4. The script computes Cohen's κ and lists disagreements.
5. J adjudicates each disagreement, recording `final_label` and `reason`. Items that remain unresolvable are labelled AMBIGUOUS and kept.
6. Files are frozen and hashed into `MANIFEST.json`. No edits are allowed after the first evaluation run; any later correction is logged as an erratum with re-run results.

## Workload estimate (to be confirmed by the authors after a 10-item pilot)
| Task | Items | Time per item | Total |
|---|---|---|---|
| W: write P5 | 170 | ~30–40 s | ~1.5–2 h |
| W: write J5 | 60 | ~15 s | ~15 min |
| A: blind label P5 + J5 | 230 | ~15–20 s | ~1–1.3 h |
| J: adjudicate (expect 10–20 % disagreement) | ~25–45 | ~1 min | ~0.5–0.75 h |
| Catalogue sanity check (Section below) | 60 | ~1 min | ~1 h |
| **Total** | | | **≈ 4–5 person-hours, spread over 3 people** |

## Catalogue HS sanity check (separate, optional but recommended)
All 43 catalogue codes exist in HS 2022. Whether each base type is *plausibly* classified under its code needs a human check, because some mappings are debatable:
- Tablet → 847130 (description requires a keyboard);
- VR Headset → 852852 (monitor);
- Graphics/Sound Card → 847180 rather than 847330 (parts);
- Freezer → 841830 (chest type only);
- Smartwatch → 851762.

One author marks each of the 60 rows `plausible / questionable / wrong`, with a note. The outcome is reported as a dataset limitation. It does **not** change labels, because evaluation is relative to the catalogue, with P2 judged against the official code.
