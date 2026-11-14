# Pilot review sheet (10 items) — readable copy

Fill in `pilot_review_sheet.csv` (one row per item per reviewer: R1, R2). Do not run LEXITAX AUDIT on these inputs. This copy is for reading only.

## P01 — product: catalogue name with a one-edit typo
- **Input:** `Wireless Headhones`
- **Expected outcome:** ANSWER HS 851830
- **Reference:** HS 2022 851830: Headphones and earphones, whether or not combined with a microphone, and sets consisting of a microphone and one or more loudspeakers
- **Label source / rule:** catalogue:products.json base_type=Wireless Headphones (subset PA, transform=typo, item PA|Wireless Headphones|typo)
- **Your judgement:** agree / disagree / unsure — if you disagree, give the outcome you think is correct and why.

## P02 — product: catalogue name, plural/reordered
- **Input:** `Hair Dryers`
- **Expected outcome:** ANSWER HS 851631
- **Reference:** HS 2022 851631: Hair-dressing apparatus; electro-thermic hair dryers
- **Label source / rule:** catalogue:products.json base_type=Hair Dryer (subset PA, transform=plural, item PA|Hair Dryer|plural)
- **Your judgement:** agree / disagree / unsure — if you disagree, give the outcome you think is correct and why.

## P03 — product: HS 2022 text of a catalogue code
- **Input:** `Hair-dressing apparatus; electro-thermic hair dryers`
- **Expected outcome:** ANSWER HS 851631
- **Reference:** HS 2022 851631: Hair-dressing apparatus; electro-thermic hair dryers
- **Label source / rule:** HS2022:851631 (subset PB, transform=none, item PB|851631|none)
- **Your judgement:** agree / disagree / unsure — if you disagree, give the outcome you think is correct and why.

## P04 — product: HS 2022 text of an unsupported subheading in a catalogue chapter
- **Input:** `Seats; parts, of wood, (other than for use in the assembly of motor vehicles as determined by the minister, other than automotive)`
- **Expected outcome:** ABSTAIN (unsupported_subheading)
- **Reference:** HS 2022 940191: Seats; parts, of wood, (other than for use in the assembly of motor vehicles as determined by the minister, other than automotive)
- **Label source / rule:** HS2022:940191 (subset PC, transform=none, item PC|940191)
- **Your judgement:** agree / disagree / unsure — if you disagree, give the outcome you think is correct and why.

## P05 — product: HS 2022 text from an unrelated chapter
- **Input:** `Nitrile-function compounds; n.e.c. heading no. 2926`
- **Expected outcome:** ABSTAIN (out_of_catalogue_chapter)
- **Reference:** HS 2022 292690: Nitrile-function compounds; n.e.c. heading no. 2926
- **Label source / rule:** HS2022:292690 (subset PD, transform=none, item PD|292690)
- **Your judgement:** agree / disagree / unsure — if you disagree, give the outcome you think is correct and why.

## P06 — product: rule-generated ambiguous product token
- **Input:** `Computer`
- **Expected outcome:** ABSTAIN (ambiguous_rule)
- **Reference:** rule:token shared by base types with HS 847141/847160/852852/854231
- **Label source / rule:** rule:token shared by base types with HS 847141/847160/852852/854231 (subset PE, transform=none, item PE|computer)
- **Your judgement:** agree / disagree / unsure — if you disagree, give the outcome you think is correct and why.

## P07 — country: CLDR localised country name (held-out alias)
- **Input:** `Curazao`
- **Expected outcome:** IDENTIFY CW; refuse: no tax data
- **Reference:** ISO 3166-1 CW
- **Label source / rule:** CLDR47:es (subset CD, transform=localised, item CD|CW|es)
- **Your judgement:** agree / disagree / unsure — if you disagree, give the outcome you think is correct and why.

## P08 — country: ISO name of a country without tax data
- **Input:** `Puerto Rico`
- **Expected outcome:** IDENTIFY PR; refuse: no tax data
- **Reference:** ISO 3166-1 PR
- **Label source / rule:** ISO3166-1(pycountry):name (subset CB, transform=none, item CB|PR|name)
- **Your judgement:** agree / disagree / unsure — if you disagree, give the outcome you think is correct and why.

## P09 — country: one-edit typo of a country name
- **Input:** `Cuiba`
- **Expected outcome:** IDENTIFY CU; refuse: no tax data
- **Reference:** ISO 3166-1 CU
- **Label source / rule:** rule:one-edit typo of Cuba (subset CC, transform=typo, item CC|CU|typo)
- **Your judgement:** agree / disagree / unsure — if you disagree, give the outcome you think is correct and why.

## P10 — country: rule-generated ambiguous country token
- **Input:** `South`
- **Expected outcome:** DO NOT IDENTIFY (ambiguous / not a country); refuse
- **Reference:** rule:token in names of GS,KR,SS,ZA
- **Label source / rule:** rule:token in names of GS,KR,SS,ZA (subset CE, transform=none, item CE|south)
- **Your judgement:** agree / disagree / unsure — if you disagree, give the outcome you think is correct and why.
