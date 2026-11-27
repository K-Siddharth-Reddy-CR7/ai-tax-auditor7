# Pilot Review Sheet — 10 items (v3, 15 Nov 2026)

**Reviewer:** one author (proposed: Author 1, Syeda Sayeeda Farhath). A second reviewer is optional (§4).
**Time:** about 1.5–2 minutes per item, so **15–20 minutes in total**.
**Record answers in:** `pilot/pilot_review_sheet.csv`. Fill in the columns `agree(Y/N/unsure)`, `corrected_outcome`, `comment` and `minutes_spent`.

## 1. What you are checking (and what you are not)
Every expected outcome below was produced automatically, by a written rule applied to a named reference source. You are checking whether **the rule gave a sensible expected outcome for this input**.

- **You do NOT need customs or tariff knowledge.**
- **Do NOT** decide which HS code a product "really" has. Product items are judged only on one question: *does this text mean the stated one of the 60 catalogue product types, or none of them?*
- **Do NOT** run LEXITAX AUDIT on these inputs.
- **Do NOT** use an AI tool to decide.

The 60 catalogue types are listed in `pilot/catalogue_base_types.csv`. For countries, the reference is ISO 3166-1, the international list of countries and their codes. The tool only has tax data for the 40 countries in `taxes.csv`.

Expected behaviours:

| Behaviour | Meaning |
|---|---|
| **ANSWER** | The tool should identify the stated catalogue type or country. |
| **DECLINE / REFUSE** | The tool should say it cannot answer: the product is not in the catalogue, the text is ambiguous, or there is no tax data. |
| **ANSWER or DECLINE** | Short forms. Either is acceptable, but naming a *different* type would be wrong. |

## 2. The ten items
| ID | Input (exact text) | Category | Expected output | Expected behaviour | Ground-truth source | Why the label is justified | What you check |
|---|---|---|---|---|---|---|---|
| P01 | `Scanner ` (trailing space) | Formatting variation (easy) | Catalogue type **Scanner** (HS 847160 in the catalogue) | ANSWER | `products.json`: base type "Scanner" | Only a trailing space was added to the catalogue name | Is this obviously the catalogue type "Scanner"? |
| P02 | `Graphics Chrd` | Spelling mistake (borderline) | **Graphics Card** (847180) | ANSWER | `products.json`: "Graphics Card"; one-letter substitution a→h | Generated from "Graphics Card" by one edit; checked not to equal any other catalogue name | Would a reader still recognise "Graphics Card"? |
| P03 | `Adapter` | Shortened name (borderline) | **WiFi Adapter** (851762), *or* decline | ANSWER or DECLINE | `products.json`: "Adapter" is a word in only one catalogue type name, "WiFi Adapter" | Rule: last word of a multi-word name, kept only if no other type name contains it | Could "Adapter" reasonably mean a *different* catalogue type? (e.g. "Battery Charger", if read as a power adapter). If yes, mark **N** and say which; this tests the rule |
| P04 | `Memoury Card` | Similar but distinct product (borderline) | **Memory Card** (852351), **not** Graphics Card or Sound Card (847180) | ANSWER | `products.json`: "Memory Card"; typo applied to the word that distinguishes it from other "… Card" types | Generated from "Memory Card" by one edit to "Memory" | Is this recognisably "Memory Card" rather than another card? |
| P05 | `Computer` | Ambiguous (ambiguous) | No type | DECLINE | Rule over `products.json`: "Computer" occurs in Desktop Computer, Computer Monitor, Computer Mouse and Computer Processor, which have four different HS codes | The word alone cannot pick one type | Do you agree that "Computer" alone is too unspecific to choose one of those four? |
| P06 | `Graphic Design & Illustration Software` | Outside catalogue, look-alike word (unsupported) | No type | DECLINE | Open Products Facts category, path *Software > Computer Software > Multimedia & Design Software > …* | Taken from a top-level branch (Software) declared disjoint from the catalogue. It shares the word "graphic" with "Graphics Card" | Is this product clearly *not* one of the 60 catalogue types? |
| P07 | `Nuts, edible; brazil nuts, fresh or dried, shelled` | Formal HS text, unrelated chapter (out-of-domain) | No type | DECLINE | HS 2022 (UN Comtrade mirror), code 080122 | Chapter 08 (fruit and nuts) contains none of the catalogue's products | Is this clearly not one of the 60 catalogue types? |
| P08 | `Nueva Zelanda` | Foreign-language country name (borderline) | **NZ** (New Zealand) | ANSWER: identify NZ, then compute (tax data exists) | Unicode CLDR 47, Spanish (`es`) name for territory NZ | CLDR is the standard Unicode list of localised country names | Is "Nueva Zelanda" New Zealand? (Spanish) |
| P09 | `People's Democratic Republic of Algeria` | Real country without tax data (unsupported) | **DZ** (Algeria) | Identify DZ, then **REFUSE** (no tax data) | ISO 3166-1 official name of DZ (via pycountry) | Algeria is not among the 40 countries in `taxes.csv` | (a) Is this Algeria? (b) Should the tool refuse, since it has no tax rates for Algeria? |
| P10 | `Sint` | Ambiguous country word (ambiguous) | No country | Do not identify; **REFUSE** | Rule over ISO 3166-1: the word occurs in "Sint Maarten (Dutch part)" (SX) and "Bonaire, Sint Eustatius and Saba" (BQ) and is not a country name itself | "Sint" ("Saint" in Dutch) alone names neither | Do you agree that "Sint" alone does not identify one country? |

Items were drawn by a seeded rule (one per stratum, `lexeval/pilot.py`), not hand-picked. Strata:

| Difficulty | Items |
|---|---|
| easy | P01 |
| borderline | P02, P03, P04, P08 |
| ambiguous | P05, P10 |
| unsupported | P06, P09 |
| out-of-domain | P07 |

No item asks for a customs classification decision.

## 3. Decision rule after the pilot
| Result | Action |
|---|---|
| Reviewer agrees with **≥ 9/10**, and any disagreement concerns one item rather than a rule | Approve freezing, after the look-alike step below |
| A disagreement shows a **rule** is wrong (e.g. P03 shows the head-noun rule picks a misleading word) | Fix the rule in code, rebuild, log the change, redraw that stratum's pilot item, and re-check only that item |
| ≥ 2 rule-level problems | Pause; review the design with the authors before any freezing |

## 4. One reviewer or two?
**One reviewer is sufficient for this pilot.** Its purpose is a sanity check that rule-derived labels are sensible. It does not produce ground truth, and it does not measure how reliably humans label. **No inter-annotator agreement will be claimed** from a single reviewer.

A second reviewer (e.g. Author 4) is *useful but not required*. It would matter only if a human decision becomes part of the ground truth, which is the case for the look-alike step below.

## 5. Second human step (after the pilot): look-alike confirmation (≈ 15–20 min)
`pilot/p7_lookalike_confirmation.csv` lists the 60 out-of-catalogue names that share a word with a catalogue type. Most are clear (e.g. "Business Cards", "Slot Machines"). A few cannot be settled by any rule, for example:
- "Motor Vehicle Parking Cameras" (a kind of video camera?);
- "Label Makers" (a kind of printer?);
- "Airsoft Gun Batteries" (lithium batteries?).

For each, mark `outside`, `could_be:<catalogue type>` or `unsure`.

**Pre-declared rule:** only `outside` items are kept; the rest are removed before freezing and listed in the build log.

This is the one place where a human judgement shapes the test set, and the paper will say so.
