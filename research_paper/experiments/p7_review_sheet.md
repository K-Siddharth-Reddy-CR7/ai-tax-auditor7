# P7 "Outside the Catalogue": Human Review Sheet — v4 (15 Nov 2026)

**Reviewer:** Author 1. **Status: IN PROGRESS.**
- Part A items 1–8 decided: 1–3 Outside, 4 Uncertain, 5–8 Outside, no comments. Recorded in `pilot/p7_lookalike_review_v4.csv`; decisions not yet applied to the benchmark.
- Items 9–16 and Part B pending.
- **Do not run `--stage build` until Part A is complete.** The builder treats the sheet as reviewed as soon as any decision exists, and would drop the undecided items.
**Time:** about 10–15 minutes in total (Part A ≈ 5 min, Part B ≈ 5–8 min).

This is **not** the optional 60-item label-quality audit. That audit is a separate idea, assessed in `research_paper/phase7_methodology_decisions.md` §4 and currently deferred.

## Why this list is not the earlier 60 items
The v3 list of 60 look-alikes came from the Open Products Facts taxonomy. Its licence **could not be established**:
- no licence statement in the file or in the taxonomy README;
- the file is partly derived from the Google Product Taxonomy, whose terms are unclear.

Following the authors' decision, that source is **withdrawn**: no Open Products Facts text is in the benchmark. The blank v3 sheet is archived at `pilot/superseded/p7_lookalike_confirmation.csv`.

P7 now uses **Unicode emoji short names** (`emoji-test.txt` 16.0, Unicode License v3), restricted to sub-groups of tangible goods. Sub-groups overlapping the catalogue domain are excluded: phone, computer, light & video, sound, music.

## Part A — look-alikes (16 items; decide each one)
A look-alike shares a whole word with one of the 60 catalogue product types. **Question for every row: "Is this genuinely outside the supported 60-product catalogue?"**

Do not assign HS codes; only decide whether it could be one of the 60 catalogue types. Record answers in `pilot/p7_lookalike_review_v4.csv` (column `reviewer_decision(Outside/Potentially in catalogue/Uncertain)`) or here.

| # | Input | Unicode group > sub-group | Catalogue type(s) it could be confused with | Decision (Outside / Potentially in catalogue / Uncertain) | Comment |
|---|---|---|---|---|---|
| 1 | card file box | Objects > office | Graphics Card; Memory Card; Sound Card | | |
| 2 | card index | Objects > office | Graphics Card; Memory Card; Sound Card | | |
| 3 | card index dividers | Objects > office | Graphics Card; Memory Card; Sound Card | | |
| 4 | couch and lamp | Objects > household | LED Lamp | | |
| 5 | credit card | Objects > money | Graphics Card; Memory Card; Sound Card | | |
| 6 | cricket game | Activities > sport | Game Controller | | |
| 7 | flower playing cards | Activities > game | Graphics Card; Memory Card; Sound Card | | |
| 8 | folding hand fan | Objects > clothing | Electric Fan | | |
| 9 | game die | Activities > game | Game Controller | | |
| 10 | hair pick | Objects > clothing | Hair Clipper; Hair Dryer | | |
| 11 | mouse trap | Objects > household | Computer Mouse | | |
| 12 | musical keyboard | Objects > musical-instrument | Keyboard | | |
| 13 | slot machine | Activities > game | Washing Machine | | |
| 14 | toothbrush | Objects > household | Electric Toothbrush | | |
| 15 | video game | Activities > game | Game Controller; Video Camera | | |
| 16 | water pistol | Activities > game | Water Heater | | |

Rows 14 ("toothbrush" vs "Electric Toothbrush") and 15 ("video game"; the emoji 🎮 depicts a gamepad) are the genuinely debatable ones. Use **Potentially in catalogue** or **Uncertain** freely.

## Part B — plain names (100 items; flag exceptions only)
These share no word with any catalogue type, but a word rule cannot catch meaning. For example, "joystick" (drawn in an earlier draft sample, not in the current one) shares no word with any catalogue type but is in substance a game controller. **Scan the list and write down any name that could be one of the 60 catalogue types.** Write them under `EXCEPTIONS:` in `pilot/p7_plain_scan_v4.txt`, then change `REVIEWED: no` to `REVIEWED: yes <name> <date>`.

1st place medal, accordion, adhesive bandage, alembic, ambulance, american football, anchor, artist palette, automobile, balance scale, banjo, bathtub, bell pepper, bento box, bicycle, billed cap, books, bowling, boxing glove, broom, bucket, bullet train, butter, carrot, clinking beer mugs, cooked rice, cookie, croissant, crutch, cup with straw, dagger, egg, falafel, ferry, file cabinet, file folder, fondue, fountain pen, garlic, gem stone, gloves, green salad, helicopter, hot beverage, hot dog, hot pepper, ice hockey, kite, kiwi fruit, knot, ledger, linked paperclips, lipstick, magic wand, metro, money bag, motorcycle, mountain cableway, mountain railway, nut and bolt, oil drum, outbox tray, page facing up, page with curl, paperclip, passenger ship, pea pod, pencil, performing arts, pick, ping pong, pool 8 ball, pot of food, poultry leg, pretzel, purse, roll of paper, round pushpin, rugby football, sandwich, satellite antenna, small airplane, soft ice cream, spaghetti, sponge, sport utility vehicle, stethoscope, teddy bear, thong sandal, toilet, top hat, tractor, train, triangular ruler, trophy, wastebasket, watermelon, window, yen banknote, yo-yo

## How these decisions shape P7 (pre-declared, enforced in code)
| Decision | Effect |
|---|---|
| Look-alike marked **Outside** | Kept in P7 with gold = DECLINE |
| Look-alike marked **Potentially in catalogue** or **Uncertain** | **Removed** from the benchmark, listed in `build_log.json` |
| Plain name listed under EXCEPTIONS | **Removed**, listed in `build_log.json` |

- Removed items are not relabelled as catalogue items, because that would be a human HS-style judgement.
- `run_all.py --stage freeze` **refuses** to run until both parts are complete.
- Current draft P7: 116 items (100 plain + 16 look-alikes; DEV 27 / TEST 89). The final size is 116 minus removals.
- The paper will report the number removed and the reason.
