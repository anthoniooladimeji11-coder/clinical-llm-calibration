"""
Build Figure 3: abstention frontier per (model, stratum), comparing
three UQ methods: verbalized confidence, self-consistency variance,
semantic entropy.

For each UQ signal, sweep abstention rates from 0% to 95% and plot
the error rate on the cases the model still answers.

Output:
  figures/abstention_frontier_v0.1.png
  results/abstention_summary_v0.1.json
"""
import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


DATA = Path("results/grading_with_uq_v0.1.jsonl")
OUT_FIG = Path("figures/abstention_frontier_v0.1.png")
OUT_SUM = Path("results/abstention_summary_v0.1.json")

MODELS = ["llama-3.1-8b", "qwen2.5-7b", "gemma2-9b", "medgemma-4b"]
STRATA = ["common", "rare", "high_acuity"]
STRATUM_LABELS = {
    "common": "Common", "rare": "Rare", "high_acuity": "High-acuity"
}

# UQ method config: (key, uncertainty_score_lambda, color, label)
# Note: verbalized confidence -> uncertainty = 100 - confidence
# Two UQ methods retained per D-026: with N=3, lexical semantic entropy
# is near-degenerate with self-consistency variance. Variance is kept as
# the representative sample-spread signal.
UQ_METHODS = [
    ("verbalized",
     lambda r: (100 - r["model_confidence"])
     if r.get("model_confidence") is not None else None,
     "#2c7fb8", "Verbalized confidence"),
    ("variance",
     lambda r: r.get("self_consistency_variance"),
     "#d95f0e", "Self-consistency variance"),
]

ABSTENTION_LEVELS = np.linspace(0, 0.95, 20)


def compute_frontier(rows: list[dict], score_fn) -> tuple[list[float], list[float]]:
    """
    For a given UQ method (score_fn returns an UNCERTAINTY score, higher = less sure),
    return parallel lists (abstention_rate, error_rate_on_answered).
    """
    scored = []
    for r in rows:
        s = score_fn(r)
        if s is None:
            continue
        scored.append((s, 0 if r["correct"] else 1))

    if not scored:
        return [], []

    scored.sort(key=lambda x: x[0])  # ascending uncertainty
    n = len(scored)

    abst_rates, err_rates = [], []
    for level in ABSTENTION_LEVELS:
        keep_n = max(1, int(round(n * (1 - level))))
        kept = scored[:keep_n]
        errors = sum(e for _, e in kept) / len(kept)
        actual_abst = 1 - keep_n / n
        abst_rates.append(actual_abst)
        err_rates.append(errors)
    return abst_rates, err_rates


def main():
    rows = []
    with open(DATA) as f:
        for line in f:
            rows.append(json.loads(line))

    by = defaultdict(list)
    for r in rows:
        by[(r["model"], r["stratum"])].append(r)

    fig, axes = plt.subplots(
        len(MODELS), len(STRATA),
        figsize=(13, 16), sharex=True, sharey=True,
    )

    summary = {}
    for mi, model in enumerate(MODELS):
        summary[model] = {}
        for si, stratum in enumerate(STRATA):
            ax = axes[mi, si]
            stratum_rows = by[(model, stratum)]
            if not stratum_rows:
                ax.set_visible(False)
                continue

            base_err = sum(0 if r["correct"] else 1
                           for r in stratum_rows) / len(stratum_rows)

            summary[model][stratum] = {"base_error_rate": base_err, "methods": {}}

            for key, score_fn, color, label in UQ_METHODS:
                abst, err = compute_frontier(stratum_rows, score_fn)
                if not abst:
                    continue
                ax.plot(abst, err, marker="o", ms=4, lw=1.6,
                        color=color, label=label, alpha=0.85)
                # Area under the abstention curve (lower = better)
                auc = np.trapezoid(err, abst) if len(abst) > 1 else float("nan")
                summary[model][stratum]["methods"][key] = {
                    "auc_error_vs_abstention": float(auc),
                    "abstention_rates": abst,
                    "error_rates": err,
                }

            # Reference line at base error rate
            ax.axhline(base_err, color="#888", ls="--", lw=1, alpha=0.6)

            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.grid(True, alpha=0.2)
            title = (f"{model}  |  {STRATUM_LABELS[stratum]}\n"
                     f"baseline error = {base_err:.1%}")
            ax.set_title(title, fontsize=9.5)
            if mi == len(MODELS) - 1:
                ax.set_xlabel("Abstention rate")
            if si == 0:
                ax.set_ylabel("Error rate on answered")
            if mi == 0 and si == len(STRATA) - 1:
                ax.legend(loc="upper right", fontsize=8, framealpha=0.95)

    fig.suptitle(
        "Abstention frontier per model and stratum\n"
        "(lower curve = better; dashed grey = no-abstention baseline)",
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

    print("\n--- AUC (lower = better) per (model, stratum, method) ---")
    for m in MODELS:
        for s in STRATA:
            if s not in summary[m]:
                continue
            mres = summary[m][s]["methods"]
            line = f"  {m:14s} {s:12s} "
            for key, _, _, _ in UQ_METHODS:
                auc = mres.get(key, {}).get("auc_error_vs_abstention",
                                            float("nan"))
                line += f"{key}={auc:.3f}  "
            print(line)


if __name__ == "__main__":
    main()
