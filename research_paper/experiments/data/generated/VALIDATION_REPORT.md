# Dataset validation report (DRAFT build — not frozen)

Errors: 0; warnings: 0

## product_benchmark.csv
- n: 6096
- by_subset_split: {'PA/dev': 155, 'PA/test': 245, 'PB/test': 68, 'PB/dev': 60, 'PC/dev': 317, 'PC/test': 567, 'PD/test': 2855, 'PD/dev': 1821, 'PE/dev': 5, 'PE/test': 3}
- texts_in_both_splits: 0
- conflicting_label_texts: 0
- groups: 1236
- groups_straddling_splits: 0
- test_items_with_near_duplicate_in_dev(jaccard>=0.9,<=12 tokens): 11

## country_benchmark.csv
- n: 2122
- by_subset_split: {'CA/test': 63, 'CA/dev': 57, 'CB/dev': 345, 'CB/test': 539, 'CC/dev': 98, 'CC/test': 149, 'CD/dev': 330, 'CD/test': 491, 'CE/test': 7, 'CE/dev': 9, 'CF/dev': 13, 'CF/test': 21}
- texts_in_both_splits: 0
- conflicting_label_texts: 0
- groups: 298
- groups_straddling_splits: 0
- test_items_with_near_duplicate_in_dev(jaccard>=0.9,<=12 tokens): 0

## reference
- hs_edition_markers: {'new_in_2022_present': {'8524': True, '8549': True, '8806': True, '851713': True, '851714': True}, 'deleted_in_2022_absent': {'851712': True, '854810': True}}
- versions: {'pycountry': '26.2.16', 'babel': '2.18.0', 'cldr': '47'}

## Build log (pre-declared exclusion rules applied)
- duplicate_removed: 126
- hs_code_excluded: 10
- label_conflict_removed: 3
- perturbation_not_applicable: 20
- typo_not_generated: 2
