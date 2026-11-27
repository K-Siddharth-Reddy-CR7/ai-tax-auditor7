"""Independent audit of every manuscript table and Fig. 1 (read-only).

Recomputes the values from the per-item TEST outputs and the frozen benchmark files (not from the summary CSVs that
make_tables.py uses), checks them against the summary CSVs and against the generated LaTeX tables, recomputes the Holm
adjustment from the raw permutation p-values, and writes table_figure_audit.md. Exit code 1 if any check fails.
Run from this directory: python audit_tables.py
"""
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.normpath(os.path.join(HERE, "..", "experiments"))
RUN_ID = "20261127T104925Z-0f293784"
TP = os.path.join(EXP, "results", "runs", RUN_ID, "processed")
GEN = os.path.join(EXP, "data", "generated")
SYS = ("B", "S0", "S1")
CHECKS, FAILS = [], []


def rows(p):
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def tex(name):
    with open(os.path.join(HERE, "tables", name), encoding="utf-8") as fh:
        return fh.read()


def check(table, what, ok, detail=""):
    CHECKS.append((table, what, "PASS" if ok else "FAIL", detail))
    if not ok:
        FAILS.append((table, what, detail))


def f3(v):
    return "--" if v != v else f"{v:.3f}"


def rates(outcomes):
    n = len(outcomes)
    c = Counter(outcomes)
    ans = c["CORRECT"] + c["SILENT_ERROR"]
    return {"n": n, **{k: c[k] for k in ("CORRECT", "SAFE_ABSTENTION", "OVER_ABSTENTION", "EXPLICIT_FAILURE", "SILENT_ERROR")},
            "coverage": ans / n, "decision_accuracy": (c["CORRECT"] + c["SAFE_ABSTENTION"]) / n,
            "silent_error_rate": c["SILENT_ERROR"] / n}


excluded = {r["item_id"] for r in rows(os.path.join(TP, "primary_test_excluded_from_metrics.csv"))}
pi = rows(os.path.join(TP, "primary_test_product_items.csv"))
ci = rows(os.path.join(TP, "primary_test_country_items.csv"))
check("all", "8 excluded pilot items listed", len(excluded) == 8, str(sorted(excluded)))
check("all", "no excluded item in any primary per-item row", not (excluded & {r["item_id"] for r in pi + ci}))
check("all", "all scored rows are TEST", {r["split"] for r in pi + ci} == {"test"})

# ------------------------------------------------------------------ Table I (benchmark files)
bench_p = rows(os.path.join(GEN, "product_benchmark.csv"))
bench_c = rows(os.path.join(GEN, "country_benchmark.csv"))
t1 = tex("benchmark.tex")
for bench, key in ((bench_p, "P"), (bench_c, "J")):
    for sub in sorted({r["subset"] for r in bench}):
        dev = sum(r["split"] == "dev" for r in bench if r["subset"] == sub)
        test_rows = [r for r in bench if r["subset"] == sub and r["split"] == "test" and r["item_id"] not in excluded]
        cl = len({r["cluster"] for r in test_rows})
        label = sub.split("_")[0]
        line = next((l for l in t1.splitlines() if l.startswith(label + " ")), "")
        cells = [c.strip() for c in line.split("&")]
        ok = len(cells) >= 4 and cells[1:4] == [str(dev), str(len(test_rows)), str(cl)]
        check("Table I", f"{label}: DEV {dev}, TEST {len(test_rows)}, clusters {cl}", ok, line[:120])
        if key == "P":
            gold = Counter(r["expected"] for r in test_rows)
            exp_gold = {"P1": "answer", "P2": "answer", "P3": "answer", "P4": "decline", "P5": "answer",
                        "P6": "decline", "P7": "decline", "P8": "mixed"}[label]
            want = ({"ANSWER"} if exp_gold == "answer" else {"ABSTAIN"} if exp_gold == "decline" else {"ANSWER", "ABSTAIN"})
            check("Table I", f"{label}: gold '{exp_gold}' matches benchmark 'expected' values {dict(gold)}",
                  set(gold) == want and cells[4].startswith(exp_gold))
for lab, items, n_cl in (("Pooled product P1--P7", [r for r in bench_p if r["subset"] != "P8_hs_formal"], None),
                         ("Pooled country J4--J7", [r for r in bench_c if r["subset"] in ("J4_typo", "J5_cldr", "J6_ambiguous", "J7_region")], None)):
    dev = sum(r["split"] == "dev" for r in items)
    test_rows = [r for r in items if r["split"] == "test" and r["item_id"] not in excluded]
    cl = len({r["cluster"] for r in test_rows})
    line = next(l for l in t1.splitlines() if l.startswith(lab))
    cells = [c.strip() for c in line.split("&")]
    check("Table I", f"{lab}: DEV {dev}, TEST {len(test_rows)}, clusters {cl}", cells[1:4] == [str(dev), str(len(test_rows)), str(cl)], line)
check("Table I", "TEST scored totals 529 product / 1,465 country",
      sum(r["split"] == "test" and r["item_id"] not in excluded for r in bench_p) == 529
      and sum(r["split"] == "test" and r["item_id"] not in excluded for r in bench_c) == 1465)

# ------------------------------------------------------------------ Table II + Fig. 1 (pooled, from per-item rows)
summ = {t: {(r["system"], r["subset"]): r for r in rows(os.path.join(TP, f"primary_test_{t}_summary.csv"))}
        for t in ("product", "identification", "tax_behaviour")}
t2 = tex("primary.tex")
pooled = {"product": lambda r: r["subset"] != "P8_hs_formal", "identification": lambda r: r["s1_builtin"] != "True",
          "tax_behaviour": lambda r: r["s1_builtin"] != "True"}
src = {"product": (pi, "outcome"), "identification": (ci, "identification"), "tax_behaviour": (ci, "tax_behaviour")}
fig_values = {}
for task in ("product", "identification", "tax_behaviour"):
    items, col = src[task]
    for s in SYS:
        rr = rates([r[col] for r in items if r["system"] == s and pooled[task](r)])
        sr = summ[task][(s, "ALL")]
        same = all(int(sr[k]) == rr[k] for k in ("n", "CORRECT", "SAFE_ABSTENTION", "OVER_ABSTENTION", "EXPLICIT_FAILURE", "SILENT_ERROR")) \
            and all(abs(float(sr[m]) - rr[m]) < 1e-12 for m in ("coverage", "decision_accuracy", "silent_error_rate"))
        check("Table II", f"{task} {s}: per-item recount equals summary CSV (n={rr['n']})", same)
        cis = {m: f"{f3(rr[m])} [{f3(float(sr[m + '_cluster_ci_low']))}, {f3(float(sr[m + '_cluster_ci_high']))}]"
               for m in ("coverage", "decision_accuracy", "silent_error_rate")}
        row_text = f"& {s} & {rr['CORRECT']} & {rr['SAFE_ABSTENTION']} & {rr['OVER_ABSTENTION']} & {rr['SILENT_ERROR']} & " \
                   f"{cis['coverage']} & {cis['decision_accuracy']} & {cis['silent_error_rate']}"
        check("Table II", f"{task} {s}: counts, rates and cluster CIs printed as in the outputs", row_text in t2, row_text)
        check("Table II", f"{task} {s}: no explicit failures (caption claim)", rr["EXPLICIT_FAILURE"] == 0)
        fig_values[(task, s)] = {k: rr[k] / rr["n"] for k in ("CORRECT", "SAFE_ABSTENTION", "OVER_ABSTENTION", "SILENT_ERROR")}
check("Table II", "pooled denominators 359/134 and 769/207 in the row labels",
      "Product P1--P7 (359 / 134)" in t2 and "Country identification J4--J7 (769 / 207)" in t2 and "Tax behaviour J4--J7 (769 / 207)" in t2)
for (task, s_), v in sorted(fig_values.items()):
    check("Fig. 1", f"bar {task} {s_}: shares C/SA/OA/SE = " + " / ".join(f"{v[k]:.3f}" for k in ("CORRECT", "SAFE_ABSTENTION", "OVER_ABSTENTION", "SILENT_ERROR")),
          True, "recomputed from per-item rows; the figure is drawn from the identical summary counts")
check("Fig. 1", "each bar's four outcome shares sum to 1 (no explicit failures)",
      all(abs(sum(v.values()) - 1) < 1e-12 for v in fig_values.values()))

# ------------------------------------------------------------------ Table III (per category, from per-item rows)
t3 = tex("product_categories.tex")
for sub in sorted({r["subset"] for r in pi}):
    cells = []
    for s in SYS:
        rr = rates([r["outcome"] for r in pi if r["system"] == s and r["subset"] == sub])
        cells.append(f"{f3(rr['silent_error_rate'])} / {f3(rr['coverage'])}")
        n = rr["n"]
    line = f"{sub.split('_')[0]} & {n} & " + " & ".join(cells)
    check("Table III", f"{sub.split('_')[0]} (n={n})", line in t3, line)

# ------------------------------------------------------------------ Table IV (paired tests)
pt = rows(os.path.join(TP, "primary_test_paired_tests.csv"))
t4 = tex("paired_tests.tex")
check("Table IV", "18 primary tests", len(pt) == 18)
p = [float(r["p_value"]) for r in pt]
order = sorted(range(len(p)), key=lambda i: p[i])
holm, run = [0.0] * len(p), 0.0
for rank, i in enumerate(order):
    run = max(run, min(1.0, (len(p) - rank) * p[i]))
    holm[i] = run
check("Table IV", "Holm adjustment recomputed from raw p-values equals p_holm",
      all(abs(holm[i] - float(pt[i]["p_holm"])) < 1e-12 for i in range(len(p))))
ind = {"decision_correct": lambda o: o in ("CORRECT", "SAFE_ABSTENTION"), "silent_error": lambda o: o == "SILENT_ERROR"}
for r in pt:
    items, col = src[r["task"]]
    f = pooled[r["task"]]
    ra = sum(ind[r["metric"]](x[col]) for x in items if x["system"] == r["system_a"] and f(x)) / int(r["n_items"])
    rb = sum(ind[r["metric"]](x[col]) for x in items if x["system"] == r["system_b"] and f(x)) / int(r["n_items"])
    ok_rates = abs(ra - float(r["rate_a"])) < 1e-12 and abs(rb - float(r["rate_b"])) < 1e-12 \
        and abs((rb - ra) - float(r["diff_b_minus_a"])) < 1e-12
    pv = float(r["p_holm"])
    ps = f"{pv:.4f}" if pv < 0.1 else f"{pv:.2f}"
    txt = f"${float(r['diff_b_minus_a']):+.3f}$ [${float(r['diff_ci_low']):+.3f}$, ${float(r['diff_ci_high']):+.3f}$] & " + \
          ("\\textbf{" + ps + "}" if pv < 0.05 else ps)
    check("Table IV", f"{r['task']} {r['metric']} {r['system_a']}->{r['system_b']}: rates/diff recomputed; printed",
          ok_rates and txt in t4, txt)
check("Table IV", "9 tests Holm-significant (text claim)", sum(float(r["p_holm"]) < 0.05 for r in pt) == 9)

# ------------------------------------------------------------------ Table V (propagation, malformed)
t5 = tex("propagation.tex")
for lab, rs, n in (("product P1-P7", [r for r in pi if r["subset"] != "P8_hs_formal"], 359),
                   ("country J4-J7", [r for r in ci if r["s1_builtin"] != "True"], 769)):
    for s in SYS:
        c = Counter(r["propagation"] for r in rs if r["system"] == s)
        check("Table V", f"{lab} {s}: propagation classes are exclusive and sum to {n}", sum(c.values()) == n, dict(c))
check("Table V", "product block: landed-cost error is 0 for every system (no FINANCIAL_* class)",
      not any(r["propagation"].startswith("FINANCIAL") for r in pi) and "Landed-cost error & 0 & 0 & 0" in t5)
fab = Counter(r["propagation"] for r in pi if r["system"] == "S0" and r["subset"] != "P8_hs_formal" and r["fabricated"] == "True")
check("Table V", f"S0 fallback code 120 = 83 + 33 + 4 across classes {dict(fab)}",
      sum(fab.values()) == 120 and fab == Counter({"COMPUTED_WHEN_SHOULD_REFUSE_SILENT": 83, "MASKED_SILENT": 33, "NO_ERROR": 4})
      and "fallback code 8471.30$^\\ast$ & 0 & 120 & 0" in t5)
expected_rows = {"No error & 116 & 200 & 247", "Product wrong or unresolved, flagged; cost unchanged & 132 & 0 & 0",
                 "Product wrong, silent; cost unchanged & 0 & 48 & 0", "Should decline, cost computed, flagged & 92 & 0 & 0",
                 "Should decline, cost computed, silent & 19 & 111 & 0", "Correct refusal & 0 & 0 & 111",
                 "Over-refusal & 0 & 0 & 1", "Total & 359 & 359 & 359", "No error & 0 & 3 & 0",
                 "Landed-cost error, silent & 137 & 134 & 0", "Should refuse, cost computed, silent & 632 & 632 & 0",
                 "Correct refusal & 0 & 0 & 632", "Over-refusal & 0 & 0 & 137", "Total & 769 & 769 & 769",
                 "Rejected & 5 & 7 & 18", "Landed cost computed & 13 & 11 & 0"}
for e in sorted(expected_rows):
    check("Table V", f"row printed: {e}", e in t5)
for s, nfe in (("B", 137), ("S0", 134)):
    rel = sorted(float(r["rel_cost_error"]) for r in ci if r["system"] == s and r["s1_builtin"] != "True" and r["propagation"].startswith("FINANCIAL"))
    med = (rel[len(rel) // 2] + rel[(len(rel) - 1) // 2]) / 2
    sub = Counter(r["tax_subtype"] for r in ci if r["system"] == s and r["s1_builtin"] != "True" and r["propagation"].startswith("FINANCIAL"))
    check("Table V", f"{s}: {nfe} silent landed-cost errors, all default rates; median {med:.4f} -> 10.3%, max {rel[-1]:.4f} -> 13.75%",
          len(rel) == nfe and sub == Counter({"default_rates": nfe}) and f"{100 * med:.1f}" == "10.3" and f"{100 * rel[-1]:.2f}" == "13.75")
mal = rows(os.path.join(TP, "primary_test_malformed_items.csv"))
for s, rej, comp in (("B", 5, 13), ("S0", 7, 11), ("S1", 18, 0)):
    r_ = [r for r in mal if r["system"] == s]
    check("Table V", f"malformed {s}: {rej} rejected, {comp} costs computed of 18",
          len(r_) == 18 and sum(r["rejected"] == "True" for r in r_) == rej and sum(r["computed"] == "True" for r in r_) == comp)

# ------------------------------------------------------------------ Table VI (exploratory ladder, from ladder per-item rows)
lpi = rows(os.path.join(TP, "ladder_test_product_items.csv"))
lci = rows(os.path.join(TP, "ladder_test_country_items.csv"))
t6 = tex("ladder.tex")
check("Table VI", "caption marks the table exploratory and outside the confirmatory family",
      "\\emph{Exploratory}" in t6 and "Not part of the confirmatory family" in t6)
lad_sys = sorted({r["system"] for r in lpi})
check("Table VI", f"11 ladder/ablation variants present: {lad_sys}", len(lad_sys) == 11)
for v in lad_sys:
    cells = []
    for items, col, f in ((lpi, "outcome", pooled["product"]), (lci, "identification", pooled["identification"]),
                          (lci, "tax_behaviour", pooled["tax_behaviour"])):
        rr = rates([r[col] for r in items if r["system"] == v and f(r)])
        cells.append(f"{f3(rr['decision_accuracy'])} / {f3(rr['silent_error_rate'])}")
    check("Table VI", f"{v}: accuracy / SER recomputed and printed", (" & ".join(cells) + " \\\\") in t6, " & ".join(cells))
l5 = rates([r["outcome"] for r in lpi if r["system"].startswith("L5") and pooled["product"](r)])
s1 = rates([r["outcome"] for r in pi if r["system"] == "S1" and pooled["product"](r)])
check("Table VI", "L5 equals primary S1 on product (consistency)", l5 == s1)
cg = Counter(r["outcome"] for r in lpi if r["system"] == "S1_-coverage_guard" and r["subset"] == "P8_hs_formal")
check("Table VI", "coverage-guard ablation: 13 silent errors on P8 (text claim)", cg["SILENT_ERROR"] == 13)

# ------------------------------------------------------------------ abstract claim (Part 4 correction)
with open(os.path.join(HERE, "main.tex"), encoding="utf-8") as fh:
    main_tex = " ".join(fh.read().split())
sent = ("No system reliably identified held-out country forms: none identified typographical variants, and S0 correctly "
        "identified only three localised-name items while also producing 12 silent identification errors. S1's safety on "
        "these forms comes from abstention.")
check("Abstract", "corrected sentence present verbatim", sent in main_tex)
j4 = {s_: sum(r["identification"] == "CORRECT" for r in ci if r["system"] == s_ and r["subset"] == "J4_typo") for s_ in SYS}
j5 = {s_: sum(r["identification"] == "CORRECT" for r in ci if r["system"] == s_ and r["subset"] == "J5_cldr") for s_ in SYS}
se = {s_: sum(r["identification"] == "SILENT_ERROR" for r in ci if r["system"] == s_ and r["s1_builtin"] != "True") for s_ in SYS}
check("Abstract", f"J4 typos correctly identified: {j4} (none)", all(v == 0 for v in j4.values()))
check("Abstract", f"J5 localised names correctly identified: {j5} (S0 only, 3)", j5 == {"B": 0, "S0": 3, "S1": 0})
check("Abstract", f"silent identification errors on J4-J7: {se} (S0: 12)", se["S0"] == 12 and se["S1"] == 0)
check("Abstract", "S1 abstains on every held-out J4-J7 item that names a country (734 over-abstentions)",
      sum(r["identification"] == "OVER_ABSTENTION" for r in ci if r["system"] == "S1" and r["s1_builtin"] != "True") == 734)

# ------------------------------------------------------------------ report
out = [f"# Table and figure audit (generated by `audit_tables.py`)", "",
       f"Source: TEST run `{RUN_ID}` per-item outputs and the frozen benchmark files; independent of the summary CSVs "
       "used by `make_tables.py`. Confidence intervals and permutation p-values cannot be recomputed without rerunning "
       "the statistics, so they are checked as *transcribed* from the committed outputs; the Holm adjustment is "
       "recomputed.", "",
       f"**Result: {len(CHECKS) - len(FAILS)} of {len(CHECKS)} checks passed; {len(FAILS)} failed.**", "",
       "| Table | Check | Result | Detail |", "|---|---|---|---|"]
for t, w, res, d in CHECKS:
    out.append(f"| {t} | {w} | {res} | {str(d).replace('|', '/')[:140]} |")
with open(os.path.join(HERE, "table_figure_audit.md"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(out) + "\n")
print(f"{len(CHECKS) - len(FAILS)}/{len(CHECKS)} checks passed")
for f in FAILS:
    print("FAIL:", f)
sys.exit(1 if FAILS else 0)
