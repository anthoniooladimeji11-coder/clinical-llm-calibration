"""
Run the high-acuity filter and save the results to disk.

Output:
  data/processed/pmc_high_acuity_v0.2.jsonl   (one case per line)
  data/processed/pmc_high_acuity_v0.2.meta.json (run metadata)

After this runs, downstream code should read from the JSONL file
and never touch the filter live again.
"""
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from datasets import load_dataset

from src.data.pmc_patients import (
    load_keyword_config,
    filter_pmc_for_high_acuity,
)


FILTER_VERSION = "v0.2"
OUTPUT_DIR = Path("data/processed")
JSONL_PATH = OUTPUT_DIR / f"pmc_high_acuity_{FILTER_VERSION}.jsonl"
META_PATH = OUTPUT_DIR / f"pmc_high_acuity_{FILTER_VERSION}.meta.json"


def _git_commit_hash() -> str:
    """Get the current git commit hash for reproducibility."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading PMC-Patients via NCBI/Open-Patients mirror...")
    ds = load_dataset("ncbi/Open-Patients", split="train")
    print(f"  Total entries: {len(ds)}")

    print("\nLoading keyword config...")
    config_path = Path("configs/high_acuity_keywords.yaml")
    config = load_keyword_config(config_path)
    print(f"  Config version: {config.get('version', 'unknown')}")
    print(f"  Conditions:     {list(config['conditions'].keys())}")

    print("\nApplying filter...")
    matched = filter_pmc_for_high_acuity(ds, config)
    print(f"  Total matched: {len(matched)}")

    counts = Counter(m["condition"] for m in matched)
    print("\nMatches per condition:")
    for cond, n in counts.most_common():
        print(f"  {cond:30s} {n:>6d}")

    print(f"\nWriting JSONL to {JSONL_PATH} ...")
    with open(JSONL_PATH, "w") as f:
        for m in matched:
            f.write(json.dumps(m) + "\n")

    metadata = {
        "filter_version": FILTER_VERSION,
        "config_version": config.get("version", "unknown"),
        "config_path": str(config_path),
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit_hash(),
        "source_dataset": "ncbi/Open-Patients (train split)",
        "total_source_entries": len(ds),
        "total_pmc_entries_filtered": len(matched),
        "counts_per_condition": dict(counts),
        "output_jsonl": str(JSONL_PATH),
    }
    print(f"Writing metadata to {META_PATH} ...")
    with open(META_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    print("\nDone.")


if __name__ == "__main__":
    main()
