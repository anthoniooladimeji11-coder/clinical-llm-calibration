"""
Phase 6 step 1: Build the harm-rating spreadsheet for the two raters
(Tonio and Dr. Iyawe).

Reads results/grading_with_uq_v0.1.jsonl, takes every WRONG answer,
normalizes the predicted_dx string, deduplicates (true_dx, predicted_dx)
pairs, and writes a CSV with one row per unique pair.

Each pair is rated independently by both raters per the locked rubric
(configs/harm_rubric.yaml v1.0, D-027).

Output:
  data/harm_matrix/harm_rating_sheet_v0.1.csv
  data/harm_matrix/harm_rating_sheet_v0.1.meta.json
"""
import csv
import json
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


GRADING = Path("results/grading_with_uq_v0.1.jsonl")
OUT_CSV = Path("data/harm_matrix/harm_rating_sheet_v0.1.csv")
OUT_META = Path("data/harm_matrix/harm_rating_sheet_v0.1.meta.json")


_PUNCT_RE = re.compile(r"[^\w\s]")


def normalize(s: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    if s is None:
        return ""
    s = s.strip().lower()
    s = _PUNCT_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def main():
    rows = []
    with open(GRADING) as f:
        for line in f:
            rows.append(json.loads(line))

    # Keep only WRONG answers. Skip rows with empty/None predicted_dx.
    wrong = []
    for r in rows:
        if r.get("correct"):
            continue
        if not r.get("model_answer"):
            continue
        pred = str(r["model_answer"]).strip()
        if not pred:
            continue
        wrong.append(r)

    # Group by normalized (true_dx, predicted_dx) pair
    # We keep ONE display form per pair (the first one we saw) so the
    # spreadsheet shows clinicians a real string, not the normalized one.
    grouped = defaultdict(lambda: {
        "true_dx_display": None,
        "predicted_dx_display": None,
        "strata": set(),
        "models": set(),
        "case_ids": [],
        "n_occurrences": 0,
    })
    for r in wrong:
        true_n = normalize(r["ground_truth"])
        pred_n = normalize(r["model_answer"])
        key = (true_n, pred_n)
        g = grouped[key]
        if g["true_dx_display"] is None:
            g["true_dx_display"] = r["ground_truth"]
            g["predicted_dx_display"] = r["model_answer"]
        g["strata"].add(r["stratum"])
        g["models"].add(r["model"])
        g["case_ids"].append(r["case_id"])
        g["n_occurrences"] += 1

    # Sort: rarest pairs (smallest n_occurrences) last so common ones come first
    pairs = sorted(
        grouped.items(),
        key=lambda kv: (-kv[1]["n_occurrences"], kv[1]["true_dx_display"]),
    )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "pair_id",
            "true_dx",
            "predicted_dx",
            "strata",
            "n_occurrences",
            "models",
            "tonio_score",      # rater 1
            "efosa_score",      # rater 2
            "rater_notes",
        ])
        for idx, ((true_n, pred_n), g) in enumerate(pairs, 1):
            w.writerow([
                f"pair_{idx:04d}",
                g["true_dx_display"],
                g["predicted_dx_display"],
                "; ".join(sorted(g["strata"])),
                g["n_occurrences"],
                "; ".join(sorted(g["models"])),
                "",  # tonio fills in
                "",  # efosa fills in
                "",
            ])

    # Stratum and model coverage stats
    by_stratum = defaultdict(int)
    by_model = defaultdict(int)
    for _, g in pairs:
        for s in g["strata"]:
            by_stratum[s] += 1
        for m in g["models"]:
            by_model[m] += 1

    meta = {
        "rating_sheet_version": "v0.1",
        "source": str(GRADING),
        "rubric": "configs/harm_rubric.yaml v1.0 (D-027)",
        "total_wrong_rows": len(wrong),
        "unique_pairs": len(pairs),
        "deduplication": "normalize: lowercase, strip punctuation, collapse whitespace",
        "pairs_per_stratum": dict(by_stratum),
        "pairs_per_model_involved": dict(by_model),
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "raters": ["Anthonio Oladimeji Gabriel (Tonio)", "Dr. Efosa Iyawe"],
        "protocol": "Both raters score independently using rubric v1.0. "
                    "Resolve disagreements >=2 by discussion; "
                    "disagreement of 1 averages or takes the higher score.",
    }
    with open(OUT_META, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Wrote rating sheet: {OUT_CSV}")
    print(f"  Total wrong rows in source : {len(wrong):,}")
    print(f"  Unique (true, predicted)   : {len(pairs):,}")
    print(f"  Pairs per stratum          : {dict(by_stratum)}")
    print(f"  Pairs per model involved   : {dict(by_model)}")
    print(f"Wrote metadata: {OUT_META}")


if __name__ == "__main__":
    main()
