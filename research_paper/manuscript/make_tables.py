"""Generate the manuscript's LaTeX tables and figure from the committed result files (read-only).

Inputs (never modified):
  ../experiments/results/runs/20261127T104925Z-0f293784/processed/*.csv  (TEST run, confirmatory)
  ../experiments/results/dev/processed/*.csv, ../experiments/results/tuning_dev.json,
  ../experiments/results/latency_dev.json                                (DEV, development analysis)
Outputs: tables/*.tex, figures/test_outcomes.pdf, and generated_values.json (every number used in the text).
Run from this directory:  python make_tables.py
"""
import csv
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.normpath(os.path.join(HERE, "..", "experiments", "results"))
RUN_ID = "20261127T104925Z-0f293784"
TP = os.path.join(RES, "runs", RUN_ID, "processed")
DP = os.path.join(RES, "dev", "processed")
os.makedirs(os.path.join(HERE, "tables"), exist_ok=True)
os.makedirs(os.path.join(HERE, "figures"), exist_ok=True)
SYS = ("B", "S0", "S1")
VALUES = {"run_id": RUN_ID}


def rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def f3(x):
    v = float(x)
    return "--" if v != v else f"{v:.3f}"


def ci(r, m):
    return f"{f3(r[m])} [{f3(r[m + '_cluster_ci_low'])}, {f3(r[m + '_cluster_ci_high'])}]"


def write(name, text):
    with open(os.path.join(HERE, "tables", name), "w", encoding="utf-8") as fh:
        fh.write(text)


def summary(path):
    return {(r["system"], r["subset"]): r for r in rows(path)}


prod = summary(os.path.join(TP, "primary_test_product_summary.csv"))
ident = summary(os.path.join(TP, "primary_test_identification_summary.csv"))
tax = summary(os.path.join(TP, "primary_test_tax_behaviour_summary.csv"))
dprod = summary(os.path.join(DP, "primary_dev_product_summary.csv"))
dident = summary(os.path.join(DP, "primary_dev_identification_summary.csv"))

# ---------------------------------------------------------------- Table: benchmark composition (DEV / TEST scored)
P_CATS = [("P1_exact", "P1 exact catalogue name", "answer"), ("P2_format", "P2 formatting variant", "answer"),
          ("P3_typo", "P3 typo", "answer"), ("P4_short", "P4 under-specified short form", "decline"),
          ("P5_confusable", "P5 confusable neighbour", "answer"), ("P6_ambiguous", "P6 ambiguous word", "decline"),
          ("P7_outside", "P7 outside catalogue", "decline"), ("P8_hs_formal", "P8 formal HS text$^\\dagger$", "mixed")]
J_CATS = [("J1_table", "J1 table name + noise$^\\ddagger$"), ("J2_iso_code", "J2 ISO alpha-2/3 code$^\\ddagger$"),
          ("J3_iso_name", "J3 ISO name$^\\ddagger$"), ("J4_typo", "J4 typo"), ("J5_cldr", "J5 CLDR localised name"),
          ("J6_ambiguous", "J6 ambiguous word (no country)"), ("J7_region", "J7 region name (no country)")]
lines = ["\\begin{table}[t]", "\\centering",
         "\\caption{Benchmark items scored per category (DEV / TEST, TEST after the eight pilot exclusions) and TEST clusters.}",
         "\\label{tab:bench}", "\\footnotesize", "\\setlength{\\tabcolsep}{3pt}",
         "\\begin{tabular}{@{}lrrrl@{}}", "\\toprule", "Category & DEV & TEST & Cl. & Gold \\\\", "\\midrule"]
for k, lab, gold in P_CATS:
    lines.append(f"{lab} & {dprod[('B', k)]['n']} & {prod[('B', k)]['n']} & {prod[('B', k)]['n_clusters']} & {gold} \\\\")
lines.append("\\midrule")
for k, lab in J_CATS:
    lines.append(f"{lab} & {dident[('B', k)]['n']} & {ident[('B', k)]['n']} & {ident[('B', k)]['n_clusters']} & ISO / none \\\\")
lines += ["\\midrule",
          f"Pooled product P1--P7 & {dprod[('B', 'ALL')]['n']} & {prod[('B', 'ALL')]['n']} & {prod[('B', 'ALL')]['n_clusters']} & \\\\",
          f"Pooled country J4--J7 & {dident[('B', 'ALL')]['n']} & {ident[('B', 'ALL')]['n']} & {ident[('B', 'ALL')]['n_clusters']} & \\\\",
          "\\bottomrule", "\\end{tabular}",
          "\\\\[2pt]\\parbox{\\columnwidth}{\\scriptsize $^\\dagger$P8 is reported separately (in-catalogue HS codes: answer; "
          "others: decline). $^\\ddagger$Forms contained in S1's own alias table; descriptive only. Malformed inputs (18) "
          "are not split. Cl.\\ = TEST clusters.}", "\\end{table}", ""]
write("benchmark.tex", "\n".join(lines))
VALUES["n"] = {"product_test_scored": sum(int(prod[('B', k)]['n']) for k, _, _ in P_CATS),
               "country_test_scored": sum(int(ident[('B', k)]['n']) for k, _ in J_CATS),
               "pooled_product": [prod[('B', 'ALL')]['n'], prod[('B', 'ALL')]['n_clusters']],
               "pooled_country": [ident[('B', 'ALL')]['n'], ident[('B', 'ALL')]['n_clusters']]}

# ---------------------------------------------------------------- Table: primary pooled TEST results
lines = ["\\begin{table*}[t]", "\\centering",
         f"\\caption{{Primary held-out TEST results (run \\texttt{{{RUN_ID}}}), pooled scopes. Point estimate "
         "[95\\% cluster-bootstrap interval]. C = correct, SA = safe abstention, OA = over-abstention, "
         "SE = silent error; no explicit failures occurred.}", "\\label{tab:primary}", "\\footnotesize",
         "\\begin{tabular}{@{}llrrrrlll@{}}", "\\toprule",
         "Task (items / clusters) & Sys. & C & SA & OA & SE & Coverage & Decision accuracy & Silent-error rate \\\\",
         "\\midrule"]
for task, tab, lab in (("product", prod, "Product P1--P7"), ("identification", ident, "Country identification J4--J7"),
                       ("tax", tax, "Tax behaviour J4--J7")):
    for i, s in enumerate(SYS):
        r = tab[(s, "ALL")]
        head = f"{lab} ({r['n']} / {r['n_clusters']})" if i == 0 else ""
        lines.append(f"{head} & {s} & {r['CORRECT']} & {r['SAFE_ABSTENTION']} & {r['OVER_ABSTENTION']} & "
                     f"{r['SILENT_ERROR']} & {ci(r, 'coverage')} & {ci(r, 'decision_accuracy')} & "
                     f"{ci(r, 'silent_error_rate')} \\\\")
        VALUES.setdefault("primary", {}).setdefault(task, {})[s] = {
            k: r[k] for k in ("n", "n_clusters", "CORRECT", "SAFE_ABSTENTION", "OVER_ABSTENTION", "EXPLICIT_FAILURE",
                              "SILENT_ERROR", "coverage", "decision_accuracy", "silent_error_rate", "selective_accuracy",
                              "coverage_cluster_ci_low", "coverage_cluster_ci_high",
                              "decision_accuracy_cluster_ci_low", "decision_accuracy_cluster_ci_high",
                              "silent_error_rate_cluster_ci_low", "silent_error_rate_cluster_ci_high")}
    if task != "tax":
        lines.append("\\midrule")
lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}", ""]
write("primary.tex", "\n".join(lines))

# ---------------------------------------------------------------- Table: per-category product (TEST)
lines = ["\\begin{table}[t]", "\\centering",
         "\\caption{Product resolution on TEST by category: silent-error rate / coverage. Small categories "
         "(P4--P6) are descriptive only.}", "\\label{tab:prodcat}", "\\footnotesize", "\\setlength{\\tabcolsep}{4pt}",
         "\\begin{tabular}{@{}lrccc@{}}", "\\toprule", "Category & $n$ & B & S0 & S1 \\\\", "\\midrule"]
for k, lab, _ in P_CATS:
    cells = [f"{f3(prod[(s, k)]['silent_error_rate'])} / {f3(prod[(s, k)]['coverage'])}" for s in SYS]
    lines.append(f"{lab.split(' ')[0]} & {prod[('B', k)]['n']} & " + " & ".join(cells) + " \\\\")
lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
write("product_categories.tex", "\n".join(lines))
VALUES["product_categories"] = {k: {s: [prod[(s, k)][m] for m in ("n", "CORRECT", "SAFE_ABSTENTION", "OVER_ABSTENTION",
                                                                  "SILENT_ERROR", "silent_error_rate", "coverage",
                                                                  "decision_accuracy")] for s in SYS} for k, _, _ in P_CATS}
VALUES["identification_categories"] = {k: {s: [ident[(s, k)][m] for m in ("n", "CORRECT", "OVER_ABSTENTION", "SILENT_ERROR")]
                                           for s in SYS} for k, _ in J_CATS}
VALUES["tax_categories"] = {k: {s: [tax[(s, k)][m] for m in ("n", "CORRECT", "SAFE_ABSTENTION", "OVER_ABSTENTION",
                                                            "SILENT_ERROR")] for s in SYS} for k, _ in J_CATS}

# ---------------------------------------------------------------- Table: 18 primary paired tests
pt = rows(os.path.join(TP, "primary_test_paired_tests.csv"))
lines = ["\\begin{table}[t]", "\\centering",
         "\\caption{The 18 primary paired comparisons on TEST: difference (B$-$A) in the rate of the named outcome "
         "[95\\% cluster-bootstrap interval] and Holm-adjusted cluster-level sign-flip permutation $p$ "
         "(10{,}000 permutations; minimum attainable 0.0018). DC = decision correct, SE = silent error.}",
         "\\label{tab:tests}", "\\footnotesize", "\\setlength{\\tabcolsep}{2.5pt}",
         "\\begin{tabular}{@{}llllr@{}}", "\\toprule", "Task & A$\\rightarrow$B & Metric & Difference & Holm $p$ \\\\",
         "\\midrule"]
names = {"product": "Product", "identification": "Ident.", "tax_behaviour": "Tax"}
prev = None
for r in pt:
    if prev and r["task"] != prev:
        lines.append("\\midrule")
    prev = r["task"]
    p = float(r["p_holm"])
    ps = f"{p:.4f}" if p < 0.1 else f"{p:.2f}"
    if p < 0.05:
        ps = "\\textbf{" + ps + "}"
    lines.append(f"{names[r['task']]} & {r['system_a']}$\\rightarrow${r['system_b']} & "
                 f"{'DC' if r['metric'] == 'decision_correct' else 'SE'} & "
                 f"${float(r['diff_b_minus_a']):+.3f}$ [${float(r['diff_ci_low']):+.3f}$, ${float(r['diff_ci_high']):+.3f}$] & {ps} \\\\")
lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
write("paired_tests.tex", "\n".join(lines))
VALUES["paired_tests"] = [{k: r[k] for k in ("task", "metric", "system_a", "system_b", "n_items", "n_clusters", "rate_a",
                                              "rate_b", "diff_b_minus_a", "diff_ci_low", "diff_ci_high", "p_value",
                                              "p_holm", "mcnemar_p_item_level")} for r in pt]
VALUES["n_holm_significant"] = sum(float(r["p_holm"]) < 0.05 for r in pt)

# ---------------------------------------------------------------- propagation, malformed (values for text + table)
pi = rows(os.path.join(TP, "primary_test_product_items.csv"))
cit = rows(os.path.join(TP, "primary_test_country_items.csv"))
prop = {}
for lab, rs in (("product_P1_P7", [r for r in pi if r["subset"] != "P8_hs_formal"]),
                ("product_P8", [r for r in pi if r["subset"] == "P8_hs_formal"]),
                ("country_J4_J7", [r for r in cit if r["s1_builtin"] != "True"])):
    prop[lab] = {}
    for s in SYS:
        sr = [r for r in rs if r["system"] == s]
        rel = sorted(float(r["rel_cost_error"]) for r in sr if r["propagation"].startswith("FINANCIAL"))
        prop[lab][s] = {"n": len(sr), "classes": dict(Counter(r["propagation"] for r in sr)),
                        "fin_rel_err_median": rel[(len(rel) - 1) // 2] if rel else None,
                        "fin_rel_err_max": rel[-1] if rel else None,
                        "fabricated_hs": sum(r.get("fabricated") == "True" for r in sr),
                        "policy_wrong": sum(r.get("policy_wrong") == "True" for r in sr),
                        "tax_subtype": dict(Counter(r["tax_subtype"] for r in sr)) if "tax_subtype" in sr[0] else None}
VALUES["propagation"] = prop
mal = rows(os.path.join(TP, "primary_test_malformed_items.csv"))
VALUES["malformed"] = {s: {"rejected": sum(r["rejected"] == "True" for r in mal if r["system"] == s),
                           "n": sum(r["system"] == s for r in mal),
                           "costs_computed": sorted(r["landing_cost"] for r in mal if r["system"] == s and r["computed"] == "True")}
                       for s in SYS}
lines = ["\\begin{table}[t]", "\\centering",
         "\\caption{Error propagation on TEST (counts of per-item classes) and malformed-input handling.}",
         "\\label{tab:prop}", "\\footnotesize", "\\setlength{\\tabcolsep}{3pt}",
         "\\begin{tabular}{@{}lrrr@{}}", "\\toprule", "Outcome & B & S0 & S1 \\\\", "\\midrule",
         "\\multicolumn{4}{@{}l}{\\emph{Product varied, country fixed (P1--P7, $n=359$)}} \\\\"]
pc = {s: prop["product_P1_P7"][s]["classes"] for s in SYS}
cc = {s: prop["country_J4_J7"][s]["classes"] for s in SYS}
def row(lab, d, keys):
    return f"{lab} & " + " & ".join(str(sum(d[s].get(k, 0) for k in keys)) for s in SYS) + " \\\\"
lines += [row("Correct output", pc, ["NO_ERROR"]),
          row("Product wrong/unresolved, cost unaffected", pc, ["MASKED_FLAGGED", "MASKED_SILENT"]),
          row("Landed-cost error", pc, ["FINANCIAL_ERROR_FLAGGED", "FINANCIAL_ERROR_SILENT"]),
          row("Cost computed, should refuse", pc, ["COMPUTED_WHEN_SHOULD_REFUSE_FLAGGED", "COMPUTED_WHEN_SHOULD_REFUSE_SILENT"]),
          "Refused: correct / over-refusal & " + " & ".join(f"{pc[s].get('EXPLICIT_REFUSAL', 0)} / {pc[s].get('OVER_REFUSAL', 0)}" for s in SYS) + " \\\\",
          "Fabricated HS code & " + " & ".join(str(prop['product_P1_P7'][s]['fabricated_hs']) for s in SYS) + " \\\\",
          "\\midrule", "\\multicolumn{4}{@{}l}{\\emph{Country varied, product fixed (J4--J7, $n=769$)}} \\\\",
          row("Correct output", cc, ["NO_ERROR"]),
          row("Silent landed-cost error", cc, ["FINANCIAL_ERROR_SILENT"]),
          row("Cost computed, should refuse", cc, ["COMPUTED_WHEN_SHOULD_REFUSE_FLAGGED", "COMPUTED_WHEN_SHOULD_REFUSE_SILENT"]),
          "Refused: correct / over-refusal & " + " & ".join(f"{cc[s].get('EXPLICIT_REFUSAL', 0)} / {cc[s].get('OVER_REFUSAL', 0)}" for s in SYS) + " \\\\",
          "\\midrule", "\\multicolumn{4}{@{}l}{\\emph{Malformed inputs ($n=18$; not held out)}} \\\\",
          "Rejected & " + " & ".join(str(VALUES['malformed'][s]['rejected']) for s in SYS) + " \\\\",
          "Landed cost computed & " + " & ".join(str(len(VALUES['malformed'][s]['costs_computed'])) for s in SYS) + " \\\\",
          "\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
write("propagation.tex", "\n".join(lines))

# ---------------------------------------------------------------- Table: exploratory ladder (TEST, separate family)
lp = summary(os.path.join(TP, "ladder_test_product_summary.csv"))
li = summary(os.path.join(TP, "ladder_test_identification_summary.csv"))
lt = summary(os.path.join(TP, "ladder_test_tax_behaviour_summary.csv"))
LAD = [("L0_S0", "L0 = S0"), ("L1_+validation", "L1 +validation"), ("L2_+iso_identification", "L2 +ISO identification"),
       ("L3_+tax_availability_refusal", "L3 +refuse w/o tax data"), ("L4_+product_abstention", "L4 +product abstention"),
       ("L5_+s1_product_tiers(=S1)", "L5 +evidence tiers = S1"), ("S1_-typo_tier", "S1 $-$typo tier"),
       ("S1_-coverage_guard", "S1 $-$coverage guard"), ("S1_+country_typo", "S1 +country typo"),
       ("S0_-token_overlap", "S0 $-$token overlap"), ("S0_-partial_country", "S0 $-$partial country")]
lines = ["\\begin{table}[t]", "\\centering",
         "\\caption{\\emph{Exploratory} attribution ladder and ablations on TEST (pooled scopes): decision accuracy / "
         "silent-error rate. Not part of the confirmatory family.}", "\\label{tab:ladder}", "\\footnotesize",
         "\\setlength{\\tabcolsep}{3pt}", "\\begin{tabular}{@{}lccc@{}}", "\\toprule",
         "Variant & Product & Ident. & Tax \\\\", "\\midrule"]
for k, lab in LAD:
    cells = [f"{f3(t[(k, 'ALL')]['decision_accuracy'])} / {f3(t[(k, 'ALL')]['silent_error_rate'])}" for t in (lp, li, lt)]
    lines.append(f"{lab} & " + " & ".join(cells) + " \\\\")
    if k.startswith("L5"):
        lines.append("\\midrule")
lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
write("ladder.tex", "\n".join(lines))
VALUES["ladder"] = {k: {t: {m: tab[(k, 'ALL')][m] for m in ("decision_accuracy", "silent_error_rate", "coverage",
                                                             "SILENT_ERROR", "OVER_ABSTENTION")}
                        for t, tab in (("product", lp), ("identification", li), ("tax", lt))} for k, _ in LAD}
VALUES["ladder_P8_coverage_guard_SE"] = lp[("S1_-coverage_guard", "P8_hs_formal")]["SILENT_ERROR"]
lad_tests = rows(os.path.join(TP, "ladder_test_paired_tests.csv"))
VALUES["ladder_tests"] = [{k: r[k] for k in ("task", "metric", "system_a", "system_b", "diff_b_minus_a", "p_holm")} for r in lad_tests]

# ---------------------------------------------------------------- sensitivity, DEV tuning and latency (values for text)
sp = rows(os.path.join(TP, "primary_sensitivity_siblings_removed_test_paired_tests.csv"))
VALUES["sensitivity"] = {"n_holm_significant": sum(float(r["p_holm"]) < 0.05 for r in sp),
                         "same_significance_pattern": [float(a["p_holm"]) < 0.05 for a in pt] == [float(b["p_holm"]) < 0.05 for b in sp],
                         "pooled": {t: {s: [r["n"], r["n_clusters"], r["decision_accuracy"], r["silent_error_rate"]]
                                        for (s, sub), r in summary(os.path.join(TP, f"primary_sensitivity_siblings_removed_test_{t}_summary.csv")).items() if sub == "ALL"}
                                    for t in ("product", "identification", "tax_behaviour")}}
with open(os.path.join(RES, "tuning_dev.json"), encoding="utf-8") as fh:
    tun = json.load(fh)
VALUES["tuning"] = {"chosen": {k: tun["chosen"][k] for k in ("product_min_coverage", "product_typo_max_edits", "product_typo_min_len",
                                                            "dev_macro_decision_accuracy", "dev_macro_silent_error_rate")},
                    "B_dev_macro_ser": tun["baseline_B_dev_macro_ser"], "B_dev_macro_acc": tun["baseline_B_dev_macro_accuracy"],
                    "n_settings": len(tun["grid"]),
                    "n_feasible": sum(e["dev_macro_silent_error_rate"] <= tun["baseline_B_dev_macro_ser"] for e in tun["grid"]),
                    "n_tied_at_max": sum(e["dev_macro_decision_accuracy"] == max(g["dev_macro_decision_accuracy"] for g in tun["grid"]) for e in tun["grid"])}
with open(os.path.join(RES, "latency_dev.json"), encoding="utf-8") as fh:
    lat = json.load(fh)
VALUES["latency_dev_median_ms"] = {w: {s: round(x["per_call_ms"]["median"], 3) for s, x in d["systems"].items()}
                                   for w, d in lat["workloads"].items()}
VALUES["dev_pooled"] = {t: {s: [tab[(s, 'ALL')][m] for m in ("decision_accuracy", "silent_error_rate", "coverage")] for s in SYS}
                        for t, tab in (("product", dprod), ("identification", dident),
                                       ("tax", summary(os.path.join(DP, "primary_dev_tax_behaviour_summary.csv"))))}

# ---------------------------------------------------------------- Figure: outcome composition per task and system (TEST)
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

plt.rcParams.update({"font.size": 7, "font.family": "serif", "pdf.fonttype": 42})
fig, axes = plt.subplots(1, 3, figsize=(3.45, 1.75), sharey=True)
outs = [("CORRECT", "correct", "#2f6db5"), ("SAFE_ABSTENTION", "safe abstention", "#9cc3e6"),
        ("OVER_ABSTENTION", "over-abstention", "#bdbdbd"), ("SILENT_ERROR", "silent error", "#c8412b")]
for ax, (tab, title) in zip(axes, ((prod, "Product P1–P7"), (ident, "Country ID J4–J7"), (tax, "Tax J4–J7"))):
    bottom = [0.0] * 3
    for key, lab, col in outs:
        vals = [int(tab[(s, "ALL")][key]) / int(tab[(s, "ALL")]["n"]) for s in SYS]
        ax.bar(range(3), vals, bottom=bottom, color=col, width=0.7, label=lab, edgecolor="white", linewidth=0.3)
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.set_xticks(range(3), SYS)
    ax.set_title(title, fontsize=7, pad=2)
    ax.set_ylim(0, 1)
    for sp_ in ("top", "right"):
        ax.spines[sp_].set_visible(False)
axes[0].set_ylabel("share of items")
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False, fontsize=6, handlelength=1, columnspacing=0.8,
           bbox_to_anchor=(0.5, -0.02))
fig.tight_layout(rect=(0, 0.1, 1, 1), w_pad=0.4)
fig.savefig(os.path.join(HERE, "figures", "test_outcomes.pdf"), bbox_inches="tight")

with open(os.path.join(HERE, "generated_values.json"), "w", encoding="utf-8") as fh:
    json.dump(VALUES, fh, indent=1, sort_keys=True)
print("tables:", sorted(os.listdir(os.path.join(HERE, "tables"))), "| holm significant:", VALUES["n_holm_significant"],
      "| sensitivity same pattern:", VALUES["sensitivity"]["same_significance_pattern"])
