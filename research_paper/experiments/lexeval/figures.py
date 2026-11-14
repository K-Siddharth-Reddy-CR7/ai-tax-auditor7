"""Result figures (generated only from processed results; no manual values).

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
    fig, axes = plt.subplots(1, len(subsets), figsize=(3.5, 1.9), sharey=True)
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


def risk_coverage(sensitivity_json, summary_csv, out_pdf):
    """S1 operating points across the tuning grid evaluated on TEST (sensitivity only, not selection)."""
    sens = json.load(open(sensitivity_json, encoding="utf-8"))
    rows = list(csv.DictReader(open(summary_csv, encoding="utf-8")))
    fig, ax = plt.subplots(figsize=(3.4, 2.3))
    xs = [p["coverage"] for p in sens["points"]]
    ys = [p["selective_risk"] for p in sens["points"]]
    ax.scatter(xs, ys, s=10, color="#9b9a95", label="S1 grid (sensitivity)", zorder=2)
    for s in ("B", "S0", "S1"):
        r = next(r for r in rows if r["system"] == s and r["subset"] == "ALL")
        cov = float(r["coverage"])
        risk = int(r["SILENT_ERROR"]) / max(int(r["answered"]), 1)
        ax.scatter([cov], [risk], s=40, marker=SYSTEM_MARKERS[s], color=SYSTEM_COLORS[s],
                   edgecolor="white", linewidth=1.5, label=s, zorder=3)
    ax.set_xlabel("coverage (answered / all)", fontsize=7, color=INK)
    ax.set_ylabel("selective risk (wrong / answered)", fontsize=7, color=INK)
    _style(ax)
    ax.legend(fontsize=6, frameon=False)
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)


def ensure_dir():
    os.makedirs(FIGURES, exist_ok=True)
