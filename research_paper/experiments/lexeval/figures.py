"""Result figures (generated only from processed results; no manual values).

Phase C figure paths (the plotting functions never load benchmark rows themselves):
- figures_for_test_run(run): TEST figures inside an open authorised run, from that run's own outputs. Before
  plotting, every item-level output of the run is checked: split 'test' only and no excluded ID.
- dev_figures(dev_dir, tuning_json, grid_json): DEV figures, i.e. the S1 full-pipeline risk-coverage figure across
  the tuning grid on DEV plus the B/S0/S1 DEV operating points. Every input must declare split 'dev'.

Palette: validated categorical slots 1-4 of the reference palette (fixed order),
plus hatching so identity survives grayscale printing.
"""
import csv
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .paths import FIGURES, RESULTS  # noqa: E402

SYSTEM_COLORS = {"B": "#2a78d6", "S0": "#eb6834", "S1": "#1baf7a"}
SYSTEM_MARKERS = {"B": "s", "S0": "^", "S1": "o"}
OUTCOME_ORDER = ["CORRECT", "SAFE_ABSTENTION", "OVER_ABSTENTION", "SILENT_ERROR"]
OUTCOME_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
OUTCOME_HATCH = ["", "//", "..", "xx"]
INK, MUTED = "#0b0b0b", "#52514e"


def _style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=7)
    ax.grid(axis="y", color="#e4e3df", linewidth=0.5)
    ax.set_axisbelow(True)


def outcome_bars(summary_csv, out_pdf, subsets, title):
    rows = list(csv.DictReader(open(summary_csv, encoding="utf-8")))
    systems = ["B", "S0", "S1"]
    fig, axes = plt.subplots(1, len(subsets), figsize=(max(3.5, 1.1 * len(subsets) + 1.2), 1.9), sharey=True,
                             squeeze=False)
    axes = axes[0]
    for ax, sub in zip(axes, subsets):
        bottoms = [0.0] * len(systems)
        for o, col, h in zip(OUTCOME_ORDER, OUTCOME_COLORS, OUTCOME_HATCH):
            vals = []
            for s in systems:
                r = next(r for r in rows if r["system"] == s and r["subset"] == sub)
                vals.append(int(r[o]) / int(r["n"]))
            ax.bar(systems, vals, bottom=bottoms, color=col, hatch=h, edgecolor="white", linewidth=1.0, width=0.7,
                   label=o.replace("_", " ").lower())
            bottoms = [b + v for b, v in zip(bottoms, vals)]
        ax.set_title(sub, fontsize=7, color=INK)
        _style(ax)
    axes[0].set_ylabel("share of items", fontsize=7, color=INK)
    axes[0].legend(fontsize=6, frameon=False, loc="upper center", bbox_to_anchor=(len(subsets) / 2, -0.18), ncol=4)
    fig.suptitle(title, fontsize=8, color=INK)
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)


class FigureInputError(ValueError):
    """A figure input has the wrong split, an excluded ID, or missing provenance."""


RISK_COVERAGE_TITLE = "S1 full-pipeline risk\u2013coverage across the tuning grid (DEV)"


def _point(cov, risk):
    return {"coverage": cov, "selective_risk": risk}


def risk_coverage_dev(grid_json, dev_summary_csv, dev_provenance_json, out_pdf):
    """DEV-only risk-coverage figure (development analysis, NOT TEST evidence).

    Grey points: every tuning-grid setting run through the FULL S1 pipeline on DEV P1-P7
    (tuning.full_pipeline_grid). Ringed: the selected setting. Coloured: B, S0 and S1 (tuned) on DEV from the
    pooled 'ALL' row of the DEV product summary (same inputs, adapter, scope and definitions). Selection itself
    used resolver-level DEV scores over P2-P7 and is not shown as such. Returns the S1 system point, the
    selected grid point and their difference (preserved as computed)."""
    grid = json.load(open(grid_json, encoding="utf-8"))
    prov = json.load(open(dev_provenance_json, encoding="utf-8"))
    if grid.get("split") != "dev" or prov.get("split") != "dev":
        raise FigureInputError("risk-coverage figure accepts DEV inputs only")
    rows = list(csv.DictReader(open(dev_summary_csv, encoding="utf-8")))
    fig, ax = plt.subplots(figsize=(3.4, 2.5))
    pts = [g["full_pipeline"]["dev_pooled_P1_P7"] for g in grid["grid"]]
    pts = [p for p in pts if p["selective_risk"] is not None]
    ax.scatter([p["coverage"] for p in pts], [p["selective_risk"] for p in pts], s=10, color="#9b9a95",
               label="S1 full pipeline, each grid setting", zorder=2)
    sel = grid["selected_full_pipeline_point"]["dev_pooled_P1_P7"]
    if sel["selective_risk"] is not None:
        ax.scatter([sel["coverage"]], [sel["selective_risk"]], s=70, facecolors="none", edgecolors=INK,
                   linewidth=1.0, label="selected setting (resolver-level rule)", zorder=4)
    sys_pts = {}
    for s in ("B", "S0", "S1"):
        r = next(r for r in rows if r["system"] == s and r["subset"] == "ALL")
        risk = int(r["SILENT_ERROR"]) / int(r["answered"]) if int(r["answered"]) else None
        sys_pts[s] = _point(float(r["coverage"]), risk)
        if risk is not None:
            ax.scatter([float(r["coverage"])], [risk], s=40, marker=SYSTEM_MARKERS[s], color=SYSTEM_COLORS[s],
                       edgecolor="white", linewidth=1.5, label=f"{s} (DEV system evaluation)", zorder=3)
    ax.set_xlabel("coverage (answered / all), DEV products P1-P7", fontsize=7, color=INK)
    ax.set_ylabel("selective risk (silent errors / answered)", fontsize=7, color=INK)
    ax.set_title(RISK_COVERAGE_TITLE, fontsize=7, color=INK)
    fig.text(0.01, -0.06, "Development analysis, not TEST evidence. Selection used resolver-level DEV scores over "
             "P2-P7 (pre-declared rule).", fontsize=5, color=MUTED)
    _style(ax)
    ax.legend(fontsize=5, frameon=False)
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    selp = _point(sel["coverage"], sel["selective_risk"])
    diff = {k: (None if sys_pts["S1"][k] is None or selp[k] is None else sys_pts["S1"][k] - selp[k])
            for k in ("coverage", "selective_risk")}
    return {"s1_system_point": sys_pts["S1"], "selected_grid_point": selp, "difference_system_minus_grid": diff}


def _check_item_outputs(proc_dir, split, exclusions_path=None):
    """Every item-level output in proc_dir must carry only `split` rows; TEST outputs must hold no excluded ID."""
    from . import eval_exclusions
    found = 0
    for f in sorted(os.listdir(proc_dir)):
        if not f.endswith("_items.csv") or f.endswith("_malformed_items.csv"):
            continue
        rows = list(csv.DictReader(open(os.path.join(proc_dir, f), encoding="utf-8")))
        found += 1
        if {r.get("split") for r in rows} - {split}:
            raise FigureInputError(f"{f}: rows from a split other than {split!r}")
        if split == "test":
            try:
                eval_exclusions.assert_no_excluded(rows, f"figure input {f}", exclusions_path)
            except eval_exclusions.EvaluationExclusionError as e:
                raise FigureInputError(str(e)) from None
    if not found:
        raise FigureInputError(f"no item-level outputs in {proc_dir}")


def _subsets(summary_csv):
    subs = sorted({r["subset"] for r in csv.DictReader(open(summary_csv, encoding="utf-8"))} - {"ALL"})
    return ["ALL"] + subs


def _record(fig_dir, made, exclusive):
    path = os.path.join(fig_dir, "figures_provenance.json")
    with open(path, "x" if exclusive else "w", encoding="utf-8") as fh:
        json.dump(made, fh, indent=2, sort_keys=True)


def _sha(path):
    import hashlib
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def figures_for_test_run(run, tag="primary"):
    """TEST outcome figures inside an open authorised run, from the run's own (exclusion-filtered) outputs."""
    from . import run_control
    run_control.require_run(run)
    proc, fig_dir = os.path.join(run.run_dir, "processed"), os.path.join(run.run_dir, "figures")
    _check_item_outputs(proc, "test", run.paths.exclusions)
    os.makedirs(fig_dir, exist_ok=True)
    made = {}
    for kind, title in (("product_summary", "TEST: product resolution"),
                        ("identification_summary", "TEST: country identification"),
                        ("tax_behaviour_summary", "TEST: tax-data behaviour")):
        src = os.path.join(proc, f"{tag}_test_{kind}.csv")
        out = os.path.join(fig_dir, f"{tag}_test_{kind}_outcomes.pdf")
        if os.path.exists(out):
            raise FileExistsError(out)
        outcome_bars(src, out, _subsets(src), title)
        made[os.path.basename(out)] = {"split": "test", "run_id": run.run_id, "input": os.path.basename(src),
                                       "input_sha256": _sha(src)}
    _record(fig_dir, made, exclusive=True)
    return made



def dev_figures(dev_dir, tuning_json, grid_json, tag="primary"):
    """DEV figures (development analysis): the full-pipeline risk-coverage figure, from DEV outputs only."""
    proc, fig_dir = os.path.join(dev_dir, "processed"), os.path.join(dev_dir, "figures")
    _check_item_outputs(proc, "dev")
    tune = json.load(open(tuning_json, encoding="utf-8"))
    grid = json.load(open(grid_json, encoding="utf-8"))
    if tune.get("split") != "dev" or grid.get("selected_setting") != tune.get("chosen"):
        raise FigureInputError("full-pipeline grid does not belong to this DEV tuning record")
    prov = os.path.join(proc, f"{tag}_dev_provenance.json")
    summary = os.path.join(proc, f"{tag}_dev_product_summary.csv")
    os.makedirs(fig_dir, exist_ok=True)
    out = os.path.join(fig_dir, "dev_risk_coverage.pdf")
    comparison = risk_coverage_dev(grid_json, summary, prov, out)
    made = {os.path.basename(out): {
        "split": "dev", "title": RISK_COVERAGE_TITLE, "note": "development analysis, not TEST evidence",
        "selection_basis": grid["selection_basis"], "selected_setting": grid["selected_setting"],
        "s1_operating_point_vs_grid": comparison,
        "inputs": {os.path.basename(p): _sha(p) for p in (tuning_json, grid_json, summary, prov)}}}
    _record(fig_dir, made, exclusive=False)
    return made


def ensure_dir():
    os.makedirs(FIGURES, exist_ok=True)
