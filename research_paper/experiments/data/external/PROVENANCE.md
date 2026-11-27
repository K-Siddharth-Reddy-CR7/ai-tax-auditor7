# External reference data — provenance

> **Superseded (15 Nov 2026):** see `research_paper/experiments/data_provenance.md` for the current, complete provenance record.

## HS 2022 subheading descriptions
- **File:** `hs2022_datasets-harmonized-system.csv` (copied unmodified)
- **SHA-256:** `e77ee9e1cfd15a42d1fadeb2c0618d10f6b9ed9aec0e5d66826dc7ef9d3126a5`
- **Obtained from:** GitHub `datasets/harmonized-system`, commit `b1be3f2531a85fb0ea17147b19c41d3641912e43`. The file was last changed by commit `a3e0d10` (2024-01-02); the HS 2022 update is commit `4287990` (2022-09-02). Retrieved 2026-11-14.
- **Licence:** ODC-PDDL-1.0 (Open Data Commons Public Domain Dedication), per `datapackage.json`.
- **Status: unofficial mirror, NOT an official WCO publication.**
  - The repository's own README says the official data is the WCO "HS Nomenclature" (PDF), and that this dataset comes from the UN Comtrade data extraction API.
  - Its `scripts/convert.py` takes the `text` field of UN Comtrade's classification JSON and keeps the part after the last `" - "`. Descriptions are therefore UN Comtrade's **abridged** texts, not the WCO legal texts.
  - We could not re-download the UN Comtrade source from this environment: `comtradeapi.un.org` and `unstats.un.org` are blocked by the session network policy.
- **Edition evidence (checked programmatically):**
  - Headings and subheadings introduced in HS 2022 are present: 8524, 8549, 8806, 8517.13, 8517.14.
  - Subheadings deleted in HS 2022 are absent: 8517.12, 8548.10.
  - The file has 5,613 six-digit rows and 1,229 four-digit rows. The WCO-reported HS 2022 totals are 5,612 subheadings and 1,228 headings (per the WCO announcement as relayed by secondary sources; still to be checked against the WCO page). The one extra row of each is the UN Comtrade placeholder for chapter 99 ("commodities not specified").
- **Known defects:** 9 six-digit codes carry descriptions duplicated from a sibling code (e.g. 8702.30 repeats 8702.20; 8704.60 repeats 8703.80). These are excluded from the benchmark by a pre-declared rule.
- **Use in this study:** source of HS-6 *labels by definition* (an item's text is the nomenclature description of its own code). It is **not** used to validate the catalogue's product→code assignments.

## ISO 3166-1 country codes and names
- **Package:** `pycountry` 26.2.16 (LGPL-2.1). It bundles the Debian `iso-codes` database (`iso3166-1.json`, 249 entries).
- **Status:** a widely used open re-publication that tracks the ISO 3166 Maintenance Agency, **not** the official ISO Online Browsing Platform, which is licensed.
- **Fields used:** `alpha_2`, `alpha_3`, `name`, `official_name`, `common_name`.

## CLDR localised territory names (held-out alias forms)
- **Package:** `babel` 2.18.0 (BSD-3), which bundles Unicode CLDR **version 47** (Unicode License v3).
- **Locales:** de, fr, es, it, nl, pt (Latin script only, so the ASCII normaliser cannot erase them).
- **Use:** only as test inputs. These names are never part of S1's alias table.
