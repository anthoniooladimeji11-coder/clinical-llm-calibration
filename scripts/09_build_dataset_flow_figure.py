"""
Build Figure 1 (draft v0.2): dataset flow diagram.

Cleaner, paper-publication style. Three columns:
  Sources -> Filtered pool -> Final stratified evaluation set.

Output: figures/dataset_flow_v0.2.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


# ---- Numbers (update as the pipeline finalizes) ----
COMMON_SRC_N = 10178
COMMON_FILT_N = "TBD"
COMMON_TARGET_N = 800

RARE_SRC_N = 1121
RARE_FILT_N = "TBD"
RARE_TARGET_N = 600

HIGH_SRC_N = 180142
HIGH_FILT_N = 1008
HIGH_TARGET_N = 600

TOTAL_N = COMMON_TARGET_N + RARE_TARGET_N + HIGH_TARGET_N


# ---- Style ----
COL_SOURCE = "#cfe0f0"
COL_FILTER = "#e8dfc7"
COL_FINAL = "#e8d5cf"
EDGE = "#2f2f2f"
ARROW = "#6a6a6a"
SUBTEXT = "#5a5a5a"


def draw_box(ax, x, y, w, h, title, n_text, subtitle, color):
    """Three-line box: title (bold), n value (large), subtitle (small italic)."""
    box = FancyBboxPatch(
        (x - w / 2, y - h / 2),
        w, h,
        boxstyle="round,pad=0.02,rounding_size=0.10",
        linewidth=1.0,
        edgecolor=EDGE,
        facecolor=color,
    )
    ax.add_patch(box)
    ax.text(x, y + 0.34, title, ha="center", va="center",
            fontsize=10.5, fontweight="bold", color="#1a1a1a")
    ax.text(x, y + 0.02, n_text, ha="center", va="center",
            fontsize=16, fontweight="bold", color="#1a1a1a")
    if subtitle:
        ax.text(x, y - 0.34, subtitle, ha="center", va="center",
                fontsize=8.5, style="italic", color=SUBTEXT,
                wrap=True)


def draw_arrow(ax, x1, y1, x2, y2):
    arrow = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>",
        mutation_scale=14,
        linewidth=1.1,
        color=ARROW,
    )
    ax.add_patch(arrow)


def main():
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis("off")

    # Columns
    x_src, x_filt, x_final = 1.7, 5.4, 9.6
    y_rows = [6.2, 4.0, 1.8]
    box_w, box_h = 2.6, 1.5

    # --- Column headers ---
    header_y = 7.5
    for x, label in [
        (x_src, "Sources"),
        (x_filt, "Filtered pool"),
        (x_final, "Stratified evaluation set"),
    ]:
        ax.text(x, header_y, label, ha="center", va="bottom",
                fontsize=12, fontweight="bold", color="#1a1a1a")

    # --- Source column ---
    draw_box(ax, x_src, y_rows[0], box_w, box_h,
             "MedQA", f"{COMMON_SRC_N:,}",
             "USMLE 4-option (English)", COL_SOURCE)
    draw_box(ax, x_src, y_rows[1], box_w, box_h,
             "RareBench", f"{RARE_SRC_N:,}",
             "RAMEDIS + MME + HMS + LIRICAL", COL_SOURCE)
    draw_box(ax, x_src, y_rows[2], box_w, box_h,
             "PMC-Patients", f"{HIGH_SRC_N:,}",
             "NCBI Open-Patients (train)", COL_SOURCE)

    # --- Filtered column ---
    common_filt_text = f"{COMMON_FILT_N}" if isinstance(
        COMMON_FILT_N, int
    ) else COMMON_FILT_N
    rare_filt_text = f"{RARE_FILT_N}" if isinstance(
        RARE_FILT_N, int
    ) else RARE_FILT_N

    draw_box(ax, x_filt, y_rows[0], box_w, box_h,
             "Common pool", common_filt_text,
             "after pediatric & duplicate exclusion", COL_FILTER)
    draw_box(ax, x_filt, y_rows[1], box_w, box_h,
             "Rare pool", rare_filt_text,
             "after HPO-to-text conversion + quality filter",
             COL_FILTER)
    draw_box(ax, x_filt, y_rows[2], box_w, box_h,
             "High-acuity pool", f"{HIGH_FILT_N:,}",
             "keyword filter v0.2: head + admission context",
             COL_FILTER)

    # --- Final evaluation set (one tall box spanning rows) ---
    final_x, final_y = x_final, 4.0
    final_w, final_h = 2.4, 5.4
    box = FancyBboxPatch(
        (final_x - final_w / 2, final_y - final_h / 2),
        final_w, final_h,
        boxstyle="round,pad=0.02,rounding_size=0.10",
        linewidth=1.0, edgecolor=EDGE, facecolor=COL_FINAL,
    )
    ax.add_patch(box)
    ax.text(final_x, final_y + 2.2, "Evaluation set",
            ha="center", va="center",
            fontsize=12, fontweight="bold", color="#1a1a1a")
    ax.text(final_x, final_y + 1.65, f"N = {TOTAL_N:,}",
            ha="center", va="center",
            fontsize=18, fontweight="bold", color="#1a1a1a")
    # Per-stratum breakdown
    ax.text(final_x, final_y + 0.7, "Common", ha="center",
            fontsize=10, fontweight="bold", color="#1a1a1a")
    ax.text(final_x, final_y + 0.35, f"n = {COMMON_TARGET_N}",
            ha="center", fontsize=12, color="#1a1a1a")
    ax.text(final_x, final_y - 0.2, "Rare", ha="center",
            fontsize=10, fontweight="bold", color="#1a1a1a")
    ax.text(final_x, final_y - 0.55, f"n = {RARE_TARGET_N}",
            ha="center", fontsize=12, color="#1a1a1a")
    ax.text(final_x, final_y - 1.1, "High-acuity", ha="center",
            fontsize=10, fontweight="bold", color="#1a1a1a")
    ax.text(final_x, final_y - 1.45, f"n = {HIGH_TARGET_N}",
            ha="center", fontsize=12, color="#1a1a1a")
    ax.text(final_x, final_y - 2.15,
            "stratified random sample\n(seed = 42)",
            ha="center", va="center",
            fontsize=8.5, style="italic", color=SUBTEXT)

    # --- Arrows: source -> filtered ---
    for y in y_rows:
        draw_arrow(ax, x_src + box_w / 2 + 0.05, y,
                   x_filt - box_w / 2 - 0.05, y)

    # --- Arrows: filtered -> final (all converge) ---
    final_left = final_x - final_w / 2 - 0.05
    target_offsets = [0.7, -0.2, -1.1]  # align with stratum labels
    for y_src_row, y_target in zip(y_rows, target_offsets):
        draw_arrow(ax, x_filt + box_w / 2 + 0.05, y_src_row,
                   final_left, final_y + y_target)

    # --- Caption ---
    ax.text(
        6.0, 0.4,
        "Figure 1 (draft v0.2): Dataset flow from open-source clinical "
        "datasets to the stratified evaluation set.\n"
        "Numbers shown as 'TBD' indicate filters not yet finalized.",
        ha="center", va="center", fontsize=9, style="italic",
        color=SUBTEXT,
    )

    out_dir = Path("figures")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "dataset_flow_v0.2.png"
    plt.savefig(out_path, dpi=220, bbox_inches="tight",
                facecolor="white")
    print(f"Figure saved to: {out_path}")
    plt.close()


if __name__ == "__main__":
    main()
