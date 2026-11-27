# Pre-Evaluation Methodology Audit (Phase 6, 15 Nov 2026)

**Scope.** This is a review of the implemented evaluation infrastructure and draft benchmarks before any freeze, tuning or evaluation.

**Status:**
- **No tuning or evaluation has been run.**
- **Nothing is frozen. The paper has not been drafted.**

## 0. Repository state
| Check | Result |
|---|---|
| Branch | `research/option-a-evaluation` (no new branch; `main` untouched; no PR, no merge, no force-push) |
| Canonical remote | `https://github.com/K-Siddharth-Reddy-CR7/ai-tax-auditor7` |
| Original B/S0 code and datasets | Byte-identical to `main@01dde8b` (`backend/tests/test_original_untouched.py`) |
| Tests | 79 passing (63 backend/S1 + 16 evaluation) |

## 1. Answers to the review questions

### 1.1 Are dev/test splits independent and leakage-resistant? — **Yes (verified), with one design note**
- Groups are assigned by a seeded hash: HS-4 heading for catalogue-derived and HS items; ISO code for countries; word or category for ambiguity items; parent category for Open Products Facts names.
- No group straddles the split.
- Validation report (draft v3): 0 identical normalised texts across splits, 0 label conflicts, 0 near-duplicates (token Jaccard ≥ 0.9) across splits for product and country.
- DEV is used only by `tune`, and only for S1's three parameters.
- *Design note:* confusable neighbours can sit in different splits (e.g. "Memory Card", heading 8523, versus "Graphics Card", heading 8471). This is not label leakage: different texts, different labels.

### 1.2 Do all systems receive identical inputs? — **Yes (verified in code)**
- Each item yields one argument tuple (text, paired canonical counterpart, price, quantity, freight), passed unchanged to every system.
- The pairing is by item index: canonical table country for the product run, canonical base-type name for the country run.
- The smoke stage confirms that every system resolves the canonical counterparts correctly and that all systems agree on landed cost for the 400 canonical transactions.

### 1.3 Do L0–L5 isolate the intended changes? — **Mostly. Three documented couplings**
- L0 ≡ S0 and L5 ≡ S1 are verified on all 400 canonical transactions and on DEV samples of both benchmarks.
- Couplings:
  1. **L2** (ISO identification) also changes the *string passed to the policy retriever*: the resolved table name instead of the raw input. This affects only the retrieved policy record, never duty, VAT or landed cost.
  2. **L3** combines refusal-without-tax-data and removal of the FX-rate=1.0 substitution. Both are "unavailable-data handling".
  3. **L4** combines removal of the fabricated HS fallback with gating costs on product resolution. Both are "product abstention".
- *Option:* split L3 and L4 into two sub-steps each (cheap, about 20 lines). Recommended only if reviewers ask; the current grouping is defensible.

### 1.4 Do the metrics distinguish the outcomes? — **Yes**
- Outcomes: CORRECT, SAFE_ABSTENTION, OVER_ABSTENTION, EXPLICIT_FAILURE, SILENT_ERROR.
- New in v3: **EITHER** for short forms, where a correct answer or an abstention is acceptable and only a wrong code counts as an error.
- Coverage, decision accuracy, silent-error rate (SER) and selective accuracy are computed separately.
- Propagation classes separate wrong-and-flagged from wrong-and-silent, and masked from financial errors.
- In this system every wrong product answer is unflagged, so "incorrect answer" = "silent error" for the product task. The paper should say so.

### 1.5 Are the CIs and tests appropriate for paired, clustered outcomes? — **No in v2. Fixed in v3**
- **Flaw found:** items are clustered. P1–P5 hold up to 2 items per product type; country forms hold many strings per country. v2 used item-level Wilson intervals and exact McNemar, which assume independence and would overstate precision.
- **Fix:**
  - primary CIs are now **cluster bootstrap** (resample clusters);
  - the primary paired test is a **cluster-level sign-flip permutation test** (exact when ≤ 16 non-zero clusters), with a cluster-bootstrap CI for the difference;
  - Holm across the 18 primary tests (3 system pairs × 2 indicators × 3 tasks);
  - Wilson and McNemar are kept but labelled item-level/secondary.
- Unit tests check that clustering widens CIs and that the permutation test behaves at the extremes.
- **Remaining:** P4 (17 test), P5 (12 test clusters), P6 (11), J6 (10) and J7 (26) are small. They are reported descriptively with wide CIs, and no significance claims are made per category.

### 1.6 Can the evaluation be reproduced from a clean environment? — **Yes (verified)**
- A fresh copy of the tree and a fresh virtual environment from the pinned `requirements.txt` (Python 3.13.18) reproduced the build, validation, smoke checks and all 79 tests.
- The benchmark files came out **byte-identical** (SHA-256 prefixes `a53c6c7b…`, `f3a184d6…`, `bb3af788…`).
- The build is also identical under different `PYTHONHASHSEED` values.
- Caveats:
  - The Open Products Facts file is downloaded from GitHub at build time (pinned commit, hash-checked).
  - Other Python versions are untested.
  - Latency is inherently machine-dependent.

## 2. Flaws found in this audit and what changed
| # | Flaw | Change | Files |
|---|---|---|---|
| F1 | Product set dominated by formal HS texts (77 %) | Redesigned into P1–P8 (855 items). P8 is capped and reported separately | `lexeval/build_products.py` (rewritten), `config.json` |
| F2 | Clustered items analysed as independent | Cluster bootstrap CIs; cluster permutation test as primary | `lexeval/stats.py`, `lexeval/evaluate.py` |
| F3 | Latency timed the evaluation adapters (B's adapter roughly doubled B's time) | `latency.raw_systems` times only the systems' own entry points | `lexeval/latency.py`, `run_all.py` |
| F4 | Short forms forced to ANSWER, although whether "Machine" *should* be answered is a judgement | EITHER outcome: only wrong codes are penalised | `lexeval/scoring.py` |
| F5 | Pooled country metrics would have mixed in S1's built-in ISO forms | `s1_builtin` field; pooled country results use held-out forms only | `lexeval/build_countries.py`, `lexeval/evaluate.py` |
| F6 | Country codes and names mixed in one subset | Split into J2 (codes) and J3 (names); `form` field on every item | `lexeval/build_countries.py` |
| F7 | Informal out-of-catalogue products absent (only legal HS text) | P7 from Open Products Facts. Look-alikes flagged, with a pre-declared human-confirmation rule | `build_products.py`, `refdata.py`, `pilot.py` |
| F8 | Pilot required two reviewers and claimed κ | One reviewer and no IAA claim. Pilot regenerated from v3 strata | `lexeval/pilot.py`, `experiments/pilot_review_sheet.md` |
| F9 | Tuning objective included trivial (P1) and out-of-register (P8) items | Tuning uses P2–P7 on DEV | `lexeval/tuning.py`, `config.json` |
| F10 | Re-running the pilot stage could overwrite reviewer decisions | Sheet is never overwritten once it contains decisions | `lexeval/pilot.py` |

S1, B and S0 code is **unchanged** in this phase.

## 3. Remaining methodological concerns (unresolved; for author decision)
1. **Tuning constraint.** S1's parameters are chosen to maximise DEV accuracy subject to DEV SER ≤ B's DEV SER. B rarely answers, so this is a strict, safety-first constraint. *Decide before freezing:* keep it, or fix an explicit tolerance (e.g. macro SER ≤ 0.02).
2. **No external string-matching baseline.** B and S0 are the authors' own systems. Reviewers may ask how S1 compares with a standard fuzzy matcher (e.g. `difflib`/`rapidfuzz` top-1 with a DEV-tuned threshold). *Recommended* optional addition "B2", about half a day of work.
3. **Designer knowledge.** The same team, with AI assistance, built S1 and the benchmark rules, and S1's behaviour on hand examples was seen during development. Mitigations:
   - rules are fixed and hashed before evaluation;
   - S1 is tuned on DEV only;
   - categories are justified independently of S1.

   The residual bias must be disclosed in the threats-to-validity section.
4. **Look-alike labels rest on one human reviewer.** This is acceptable if disclosed. A second reviewer for those 60 items only (≈ 15 min) would allow an agreement figure.
5. **Synthetic variation.** Typo, formatting and short-form generators may not reflect real data-entry errors.
6. **Product and country errors are evaluated in separate controlled runs.** Joint errors (wrong product *and* wrong country) are not studied; this is a stated scope limit.
7. **Reference limitations.**
   - The HS mirror is unofficial; upstream verification is blocked in this environment.
   - The Open Products Facts licence is uncertain.
   - The catalogue's HS assignments are unverified.
   - Tax rates are unsourced, so financial propagation is relative to the project's own table.
8. **Small categories** (P4–P6, J6–J7) support only descriptive statements.

## 4. Minimum human review
| Step | Who | Items | Time | Required? |
|---|---|---|---|---|
| Pilot (`experiments/pilot_review_sheet.md`) | One reviewer, proposed Author 1 | 10 | 15–20 min | **Yes, before freeze** |
| Look-alike confirmation (`pilot/p7_lookalike_confirmation.csv`) | Same reviewer | 60 | 15–20 min | **Yes, unless the authors choose to drop the 60 look-alikes** |
| 60-item label audit | — | 60 | — | **Deferred.** Triggered only if the pilot finds a rule-level problem |
| Catalogue HS plausibility | — | 60 | 45–60 min | Optional (limitation stated either way) |

**Estimated time from Author 1: about 30–40 minutes.** Authors 2 and 3 are not needed. Human checks verify the labelling *rules*; they do not replace traceable ground truth.

## 5. Authorship and disclosure notes (unchanged policy)
- **Author list:**
  1. Syeda Sayeeda Farhath
  2. Siddharth Karanam
  3. P. Naga Bhargav Reddy
  4. Baalne Anjali
- All authors: Dept. of CSE, Vardhaman College of Engineering, Hyderabad.
- Author 1 is the *proposed* corresponding author, pending confirmation. No funding statement will be written until confirmed.
- **Author 4** (faculty mentor) qualifies only if she substantively reviews and revises the manuscript and approves the final version. Institutional guidance alone is not sufficient.
- AI assistance (code, benchmark generators, documents) must be disclosed truthfully per IEEE and venue policy.

## 6. Recommendation
- **Ready for pilot review: YES.**
- **Ready for freeze: NO.** Freezing needs:
  1. the pilot outcome;
  2. look-alike confirmation (or a decision to drop the 60 look-alikes);
  3. the tuning-constraint decision (§3.1);
  4. a decision on the optional external baseline (§3.2);
  5. acceptance of the Open Products Facts licence caveat;
  6. a decision on HS upstream verification: accept the stated limitation, or provide UN Comtrade `H6.json`.

## 7. Commands
To be run only after the corresponding approval:
```bash
cd research_paper/experiments
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
export PYTHONDONTWRITEBYTECODE=1
# (a) re-check the draft and regenerate the pilot sheets (no evaluation)
python run_all.py --stage build && python run_all.py --stage validate
python run_all.py --stage smoke && python run_all.py --stage pilot
python -m pytest -q tests ../../backend/tests
# (b) after the reviewer has filled pilot/pilot_review_sheet.csv and pilot/p7_lookalike_confirmation.csv:
python run_all.py --stage build      # applies the look-alike decisions (pre-declared rule)
python run_all.py --stage validate
# (c) only after explicit author approval of the freeze:
python run_all.py --stage freeze --approved-by "<author name>"
```
`tune` and `evaluate` remain blocked until (c).
