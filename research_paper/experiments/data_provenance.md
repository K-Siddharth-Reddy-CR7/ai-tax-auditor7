# Data Provenance and Permissible Claims (v4, 15 Nov 2026)

This document supersedes `data/external/PROVENANCE.md`, which is kept for history. Every source is listed with its exact version, licence, how it is used, and what may and may not be claimed from it.

## 1. HS 2022 subheading descriptions (unofficial mirror)
| Field | Value |
|---|---|
| Repository | `https://github.com/datasets/harmonized-system` (community "core datasets" package, datahub.io) |
| Commit used | `b1be3f2531a85fb0ea17147b19c41d3641912e43` (HEAD on 14 Nov 2026) |
| File | `data/harmonized-system.csv`, last changed in commit `a3e0d10` (2024-01-02, "remove inner quote at line 5351"). The HS 2022 content was added in commit `4287990` (2022-09-02, "Update harmonized system data for 2022 version") |
| SHA-256 | `e77ee9e1cfd15a42d1fadeb2c0618d10f6b9ed9aec0e5d66826dc7ef9d3126a5` |
| Copy in this repo | `data/external/hs2022_datasets-harmonized-system.csv` (unmodified) + `hs2022_datapackage.json` |
| Licence | ODC-PDDL-1.0 (public-domain dedication), as declared in `datapackage.json` |
| Stated upstream | UN Comtrade data extraction API classification file. The repository README says official HS data is the WCO "HS Nomenclature" PDF and that this dataset comes from UN Comtrade |
| Transformation by the mirror | `scripts/convert.py` keeps the text after the last `" - "` of UN Comtrade's `text` field, so descriptions are **abridged UN Comtrade texts** |
| Edition evidence (checked by code, `refdata.edition_markers`) | Present: 8524, 8549, 8806, 8517.13, 8517.14 (all introduced in HS 2022). Absent: 8517.12, 8548.10 (deleted in HS 2022). 5,613 six-digit and 1,229 four-digit rows, against the WCO-reported 5,612 subheadings and 1,228 headings (as relayed by secondary sources), plus one UN Comtrade chapter-99 placeholder. *The WCO figures have not been checked against WCO's own page.* |
| Known defects | 9 subheadings carry a sibling's description (e.g. 8702.30 = 8702.20 text), so they are excluded by rule. Some texts contain odd fragments (e.g. 9401.91 "as determined by the minister") |
| Could we verify against the upstream? | **No, not from this environment.** `comtradeapi.un.org`, `unstats.un.org` and `wcoomd.org` are blocked by the session network policy |

**What may be claimed:**
- "HS-6 codes and abridged descriptions as published by UN Comtrade for HS 2022, obtained via an unofficial public-domain conversion (`datasets/harmonized-system` @ `b1be3f2`)."
- "Each of the 43 catalogue codes appears in that listing."
- "A P8 item's text is the listed description of its own code", so P8 labels hold by definition.

**What may NOT be claimed:**
- That this is the official WCO text or legal nomenclature.
- That any product→code assignment (including the catalogue's) is a correct customs classification.
- That the project validates or performs legal customs classification.
- Anything about tariff rates.

**Better publicly accessible sources** (none substituted; for author decision):
1. **UN Comtrade reference file `H6.json`.** This is the mirror's own upstream, an official UN statistical publication, freely downloadable. *Recommended*: the mirror can be checked code-by-code and text-by-text against it. That needs an author to download it, or the authors to allow `comtradeapi.un.org` for this environment.
2. **UNSD HS 2022 classification/correlation tables.** Official UN, freely downloadable.
3. **WCO HS Nomenclature 2022 edition.** The legal text, but subject to WCO copyright; suitable for consultation, not redistribution.
4. **National tariff schedules** (e.g. USITC HTS, EU Combined Nomenclature). Official and public, but national 8/10-digit extensions; would need care to reduce to HS-6.

If none of these is adopted, the limitation stays as stated above.

## 2. ISO 3166-1 country codes and names
| Field | Value |
|---|---|
| Package | `pycountry` 26.2.16 (LGPL-2.1), pinned |
| Data | Bundled Debian `iso-codes` database (`iso3166-1.json`): 249 countries; fields alpha_2, alpha_3, name, official_name, common_name |
| Status | Open re-publication tracking the ISO 3166 Maintenance Agency. **Not** the licensed ISO Online Browsing Platform |
| Use | (a) labels for J1–J4, J6; (b) **S1's own alias table**. Hence J1–J3 are "by construction" for S1 and excluded from generalisation claims |
| May claim | "Country codes/names per ISO 3166-1 as distributed in pycountry 26.2.16" |
| May not claim | Official ISO publication; anything about sub-national territories (out of scope) |

## 3. Unicode CLDR localised territory names
| Field | Value |
|---|---|
| Package | `babel` 2.18.0 (BSD-3), bundling **CLDR 47** (Unicode License v3) |
| Locales | de, fr, es, it, nl, pt (Latin script) |
| Use | J5 test inputs (**held out**: never in S1's table); J7 region names |
| Exclusions | Names equal to an ISO/table alias (not held out); names whose normalised form maps to different countries across locales (e.g. German "Island" = Iceland vs English "island") |

## 4. Unicode emoji short names (P7 outside-catalogue names)
| Field | Value |
|---|---|
| Repository | `https://github.com/unicode-org/unicodetools` |
| Commit pinned | `ccc86e576dcadf94ef9f86969e7b5cb51e432ddc` (main, 15 Nov 2026) |
| File | `unicodetools/data/emoji/16.0/emoji-test.txt` (Emoji 16.0, dated 2024-08-14), SHA-256 `24f0c534e86cf142e2496953e8f0e46a3e702392911eddcd29c6cced85139697` |
| Licence | **Unicode License v3**: permission to use, copy, modify, publish, distribute, provided the copyright and permission notice appear with copies. Notice saved in `data/external/UNICODE_LICENSE_V3.txt` |
| Handling | Downloaded at build time from the pinned commit and hash-checked (`refdata.ensure_unicode_emoji`, git-ignored cache). 116 short names appear in the benchmark CSV, with the licence notice kept in the repository |
| Use | P7 inputs from 26 pre-declared sub-groups of tangible goods; overlapping sub-groups and abstract names excluded |
| May claim | "Out-of-catalogue product names taken from Unicode CLDR emoji short names (Emoji 16.0)" |
| May not claim | That these are invoice lines, customs declarations or a representative sample of traded goods |

### 4a. Withdrawn: Open Products Facts category taxonomy
Considered in Phase 6 and **withdrawn on 15 Nov 2026**, because its licence could not be established:
- no licence statement in the file or in `taxonomies/README.md`;
- repository code is AGPL-3.0;
- the file is partly generated from the Google Product Taxonomy, whose terms are unclear.

No Open Products Facts text remains in the code path or the benchmark.

## 5. Project datasets (inputs to the systems, unchanged)
| Dataset | Nature | Notes |
|---|---|---|
| `products.json/csv` (1,200) | **Synthetic** catalogue: 60 types × 20 name variants | HS codes exist in HS 2022, but the type→code mapping is unverified (some debatable) |
| `taxes.json/csv` (40) | **Unsourced** prototype rates | EU members carry different duty rates (internally inconsistent). Results are "correct relative to the project's table" only |
| `trade_policies.json/csv` (240) | Placeholder, identical texts | Retrieval relevance not evaluated |
| `sample_transactions.json/csv` (400) | **Synthetic**, arithmetic sequences | Only numeric fields are reused, in propagation runs |
| `EXCHANGE_RATES` in `server.py` | Unsourced, undated | 5 currencies missing |

## 6. Generated benchmark (this study)
- **Generator:** `research_paper/experiments/lexeval/build_*.py`, written with AI assistance and reviewed by the authors (pending).
- **Determinism:** fixed seed 20261114; deterministic across Python hash seeds; reproduced byte-identically in a fresh virtual environment from `requirements.txt` (15 Nov 2026).
- **Labels:** **reference-derived or rule-derived** only. No label comes from any system output, and none is a free-form model suggestion. Human checks: the 10-item pilot and the look-alike confirmation (pending).
- **Not a real-world customs dataset.** It contains no customs declarations.
