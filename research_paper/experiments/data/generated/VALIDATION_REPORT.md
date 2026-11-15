# Dataset validation report (DRAFT build — not frozen)

Errors: 0; warnings: 0

## product_benchmark.csv
- n: 809
- by_subset_split: {'P1_exact/dev': 44, 'P1_exact/test': 76, 'P2_format/dev': 44, 'P2_format/test': 76, 'P3_typo/dev': 44, 'P3_typo/test': 76, 'P4_short/dev': 14, 'P4_short/test': 16, 'P5_confusable/dev': 21, 'P5_confusable/test': 22, 'P6_ambiguous/test': 11, 'P6_ambiguous/dev': 6, 'P7_outside/dev': 27, 'P7_outside/test': 89, 'P8_hs_formal/test': 171, 'P8_hs_formal/dev': 72}
- texts_in_both_splits: 0
- conflicting_label_texts: 0
- groups: 304
- groups_straddling_splits: 0
- test_items_with_near_duplicate_in_dev(jaccard>=0.9,<=12 tokens): 0

## country_benchmark.csv
- n: 2122
- by_subset_split: {'J1_table/test': 81, 'J1_table/dev': 39, 'J2_iso_code/test': 344, 'J3_iso_name/test': 272, 'J2_iso_code/dev': 154, 'J3_iso_name/dev': 114, 'J4_typo/test': 170, 'J4_typo/dev': 77, 'J5_cldr/test': 564, 'J5_cldr/dev': 257, 'J6_ambiguous/test': 10, 'J6_ambiguous/dev': 6, 'J7_region/test': 26, 'J7_region/dev': 8}
- texts_in_both_splits: 0
- conflicting_label_texts: 0
- groups: 298
- groups_straddling_splits: 0
- test_items_with_near_duplicate_in_dev(jaccard>=0.9,<=12 tokens): 0

## reference
- hs_edition_markers: {'new_in_2022_present': {'8524': True, '8549': True, '8806': True, '851713': True, '851714': True}, 'deleted_in_2022_absent': {'851712': True, '854810': True}}
- versions: {'pycountry': '26.2.16', 'babel': '2.18.0', 'cldr': '47'}

## Build log (pre-declared exclusion rules applied)
- duplicate_removed: 127
- emoji_pool_sizes: 1
- hs_code_excluded: 10
- label_conflict_removed: 3
- typo_not_generated: 2
