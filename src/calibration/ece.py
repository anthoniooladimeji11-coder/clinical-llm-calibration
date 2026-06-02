"""
Expected Calibration Error (ECE) and binning utilities.

ECE measures the gap between predicted confidence and actual accuracy.
We use equal-width binning over confidence (10 bins from 0 to 100).
"""
import numpy as np


def compute_bins(
    confidences: np.ndarray,
    corrects: np.ndarray,
    n_bins: int = 10,
) -> dict:
    bin_edges = np.linspace(0, 100, n_bins + 1)
    bin_indices = np.digitize(confidences, bin_edges) - 1
    bin_indices = np.clip(bin_indices, 0, n_bins - 1)

    bin_acc = np.zeros(n_bins)
    bin_conf = np.zeros(n_bins)
    bin_counts = np.zeros(n_bins, dtype=int)

    for b in range(n_bins):
        mask = bin_indices == b
        if mask.any():
            bin_acc[b] = corrects[mask].mean()
            bin_conf[b] = confidences[mask].mean() / 100.0
            bin_counts[b] = mask.sum()

    return {
        "bin_edges": bin_edges,
        "bin_centers": (bin_edges[:-1] + bin_edges[1:]) / 2,
        "bin_counts": bin_counts,
        "bin_acc": bin_acc,
        "bin_conf": bin_conf,
    }


def expected_calibration_error(
    confidences: np.ndarray,
    corrects: np.ndarray,
    n_bins: int = 10,
) -> float:
    if len(confidences) == 0:
        return float("nan")
    bins = compute_bins(confidences, corrects, n_bins)
    n_total = bins["bin_counts"].sum()
    ece = 0.0
    for b in range(n_bins):
        w = bins["bin_counts"][b] / n_total
        gap = abs(bins["bin_conf"][b] - bins["bin_acc"][b])
        ece += w * gap
    return float(ece)
