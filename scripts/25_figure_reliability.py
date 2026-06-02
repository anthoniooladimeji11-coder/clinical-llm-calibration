"""
Build Figure 2: reliability diagrams per (model, stratum), plus ECE.
"""
import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.calibration.ece import compute_bins, expected_calibration_error

GRADING = Path("results/grading_v0.1.jsonl")
OUT_FIG = Path("figures/reliability_diagrams_v0.1.png")
OUT_SUM = Path("results/calibration_summary_v0.1.json")

MODELS = ["llama-3.1-8b", "qwen2.5-7b", "gemma2-9b", "medgemma-4b"]
STRATA = ["common", "rare", "high_acuity"]
STRATUM_LABELS = {"common": "Common", "rare": "Rare", "high_acuity": "High-acuity"}
STRATUM_COLORS = {"common": "#5e8fb3", "rare": "#c5a25b", "high_acuity": "#b3624f"}


def load_grading() -> list[dict]:
    rows = []
    with open(GRADING) as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def collect(rows: list[dict]) -> dict:
    by = defaultdict(lambda: defaultdict(lambda: ([], [])))
    for r in rows:
        if r["model_confidence"] is None:
            continue
        conf = float(r["model_confidence"])
        c = 1 if r["correct"] else 0
        confs, corrs = by[r["model"]][r["stratum"]]
        confs.append(conf)
        corrs.append(c)
    return {
        m: {s: (np.array(by[m][s][0]),
                np.array(by[m][s][1])) for s in STRATA}
        for m in MODELS
    }


def main():
    rows = load_grading()
    data = collect(rows)

    fig, axes = plt.subplots(
        len(MODELS), len(STRATA),
        figsize=(13, 16), sharex=True, sharey=True,
    )

    summary = {}
    for mi, model in enumerate(MODELS):
        summary[model] = {}
        for si, stratum in enumerate(STRATA):
            ax = axes[mi, si]
            conf, corr = data[model][stratum]
            if len(conf) == 0:
                ax.set_visible(False)
                continue

            bins = compute_bins(conf, corr, n_bins=10)
            ece = expected_calibration_error(conf, corr, n_bins=10)
            acc = float(corr.mean())
            mean_conf = float(conf.mean()) / 100.0

            summary[model][stratum] = {
                "n": int(len(conf)),
                "accuracy": acc,
                "mean_confidence": mean_conf,
                "ece": ece,
                "calibration_gap": mean_conf - acc,
            }

            ax.plot([0, 1], [0, 1], color="#888", lw=1, ls="--",
                    alpha=0.7, zorder=1)

            centers = bins["bin_centers"] / 100.0
            counts = bins["bin_counts"]
            if counts.max() > 0:
                ax.bar(centers, counts / counts.max() * 0.3,
                       width=0.09, alpha=0.15,
                       color=STRATUM_COLORS[stratum], zorder=2)

            non_empty = bins["bin_counts"] > 0
            ax.plot(bins["bin_conf"][non_empty], bins["bin_acc"][non_empty],
                    marker="o", lw=2, ms=8,
                    color=STRATUM_COLORS[stratum], zorder=3)

            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_aspect("equal")
            ax.grid(True, alpha=0.2)

            title = (f"{model}  |  {STRATUM_LABELS[stratum]}\n"
                     f"acc={acc:.1%}  conf={mean_conf:.1%}  ECE={ece:.3f}")
            ax.set_title(title, fontsize=9.5)

            if mi == len(MODELS) - 1:
                ax.set_xlabel("Confidence")
            if si == 0:
                ax.set_ylabel("Accuracy")

    fig.suptitle(
        "Reliability diagrams per model and stratum\n"
        "(dashed line = perfect calibration; below the line = overconfident)",
        fontsize=12, y=0.995,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.98])

    OUT_FIG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_FIG, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Figure saved to: {OUT_FIG}")

    OUT_SUM.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_SUM, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved to: {OUT_SUM}")

    print("\n--- Calibration summary ---")
    print(f"  {'model':14s} {'stratum':12s} {'n':>4s} "
          f"{'acc':>7s} {'conf':>7s} {'ECE':>7s} {'gap':>7s}")
    for m in MODELS:
        for s in STRATA:
            if s not in summary[m]:
                continue
            v = summary[m][s]
            print(f"  {m:14s} {s:12s} {v['n']:>4d} "
                  f"{v['accuracy']:>7.1%} {v['mean_confidence']:>7.1%} "
                  f"{v['ece']:>7.3f} {v['calibration_gap']:>+7.3f}")


if __name__ == "__main__":
    main()
