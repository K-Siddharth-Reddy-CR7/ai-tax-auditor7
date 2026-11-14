# Labelling and Human-Verification Workflow — v2 (minimal human workload)

v1, which had student authors write and double-annotate about 230 items, is **withdrawn**. The student authors are unavailable, and automation can supply traceable labels for almost everything.

## 1. Where each label comes from
| Label type | Produced by | Human needed? | Why automation is (or isn't) enough |
|---|---|---|---|
| HS-6 of an HS 2022 text (PB) | The text *is* the nomenclature description of that code | No | Correspondence holds by definition. The caveat is that texts are UN Comtrade abridgements |
| ABSTAIN for unsupported subheadings and other chapters (PC, PD) | Code ∉ catalogue codes → no correct six-digit answer exists in the system | No | Set membership; no judgement involved |
| Catalogue record for catalogue-name variants (PA) | Generator knows the source record; perturbations are label-preserving by construction and checked for collisions | Pilot spot-check | Rules could, in principle, produce an unreadable variant. The pilot and audit estimate how often |
| Ambiguous product/country tokens (PE, CE) | Pre-declared rule (token shared by ≥ 2 entities with different labels and not itself a name) | Pilot spot-check | The rule's *reasonableness* is a human judgement |
| Country ISO code (CA–CD) | ISO 3166-1 field or CLDR territory code | Pilot spot-check | Reference-defined; check that typos remain recognisable |
| Non-country regions (CF) | CLDR region codes | No | Reference-defined |
| Tax-data availability | ISO code ∈ 40-country table | No | Set membership |
| **Whether the catalogue's HS assignment is plausible** for each of the 60 product types | — | **Yes (optional)** | Requires classification expertise. Neither code existence nor string matching can establish it |

Labels are **rule-derived**. The rules were written with AI assistance and are applied deterministically. They are not presented as independently verified ground truth until the human checks below are done, and the paper will state exactly which checks were performed.

## 2. Pre-declared ambiguity criteria
Fixed before any evaluation.
- **Product (PE):** a lower-case alphabetic token of ≥ 3 characters that occurs in the names of base types mapping to ≥ 2 different HS-6 codes, and is not itself a base-type name. Expected: abstain.
- **Country (CE):** a token of ≥ 4 letters that occurs in the ISO `name`/`common_name` of ≥ 2 countries and is not itself an ISO alias or table name. Expected: no identification, refuse. Tokens are grouped by singular form for splitting.
- **Conflicts:** if two generated texts normalise identically but carry different labels, all copies are removed (e.g. CLDR German "Island" = Iceland versus the English ambiguous token "island").

## 3. Human tasks and minimum workload
| # | Task | Who (proposed; not assumed) | Items | Estimated time | Status |
|---|---|---|---|---|---|
| H1 | **10-item pilot**: agree/disagree with each expected outcome, given the input and its reference evidence (`experiments/pilot/`) | 2 reviewers independently, e.g. Author 1 and Author 4 | 10 | 15–20 min each, **≈ 35 min total** | **Required before freezing** |
| H2 | Stratified label audit (6 per stratum × 10 strata), excluding pilot items | 1 reviewer | 60 | 45–60 min | Recommended. Gives a label-error estimate with a Wilson CI |
| H3 | Catalogue HS plausibility (`experiments/pilot/catalogue_base_types.csv`) | 1 reviewer, ideally with trade/classification familiarity | 60 | 45–60 min | Optional. Reported as a dataset limitation either way |

**Minimum:** H1 only, about 35 minutes of human time. **Recommended:** H1 + H2, about 1.5 hours.

The student authors are **not** required for any of these. If no one does H2, the paper says that labels were rule-derived and pilot-checked only.

## 4. Pilot procedure
1. Reviewers read `pilot/PILOT_INSTRUCTIONS.md` and `pilot/PILOT_SHEET_READABLE.md`.
2. Each reviewer fills their rows in `pilot/pilot_review_sheet.csv` (R1 or R2) without conferring: agree/disagree/unsure, a corrected outcome if they disagree, comment, minutes.
3. Agreement (raw and Cohen's κ against the expected labels) and time are summarised. With 10 items, κ is descriptive only.
4. **Decision rule:**
   - If both reviewers agree with ≥ 9/10 and no labelling *rule* is shown to be wrong, the authors approve freezing: `run_all.py --stage freeze --approved-by "<name>"`.
   - If a rule is wrong, it is fixed in code, the draft is rebuilt, the change is logged in `IMPLEMENTATION_CHANGES.md`, and a new pilot item is drawn for that stratum.
5. After freezing, labels are immutable. Later corrections are logged as errata, and affected results are re-run and reported.

## 5. Pilot items (drawn by seeded stratified rule from DEV)
| ID | Stratum | Input | Expected |
|---|---|---|---|
| P01 | catalogue name + typo | Wireless Headhones | ANSWER 851830 |
| P02 | catalogue name, plural | Hair Dryers | ANSWER 851631 |
| P03 | HS text of catalogue code | Hair-dressing apparatus; electro-thermic hair dryers | ANSWER 851631 |
| P04 | unsupported subheading (ch. 94) | Seats; parts, of wood, (other than … automotive) | ABSTAIN |
| P05 | other chapter | Nitrile-function compounds; n.e.c. heading no. 2926 | ABSTAIN |
| P06 | ambiguous product token | Computer | ABSTAIN |
| P07 | CLDR name (es) | Curazao | IDENTIFY CW; refuse (no tax data) |
| P08 | ISO name, no tax data | Puerto Rico | IDENTIFY PR; refuse |
| P09 | country typo | Cuiba | IDENTIFY CU; refuse |
| P10 | ambiguous country token | South | do not identify; refuse |

Note for reviewers: P04's UN Comtrade text contains the national-looking phrase "as determined by the minister". This illustrates the abridgement caveat, and reviewers should comment on it.
