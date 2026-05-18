"""
Run the high-acuity filter against PMC-Patients and report:
- Total cases matched per condition
- 2 random sample cases per condition for manual sanity-checking
"""
import random
from collections import Counter
from pathlib import Path

from datasets import load_dataset

from src.data.pmc_patients import (
    load_keyword_config,
    filter_pmc_for_high_acuity,
)


def main():
    random.seed(42)

    print("Loading PMC-Patients via NCBI/Open-Patients mirror...")
    ds = load_dataset("ncbi/Open-Patients", split="train")
    print(f"  Total entries: {len(ds)}")

    print("\nLoading keyword config...")
    config = load_keyword_config(Path("configs/high_acuity_keywords.yaml"))
    print(f"  Conditions: {list(config['conditions'].keys())}")

    print("\nApplying filter...")
    matched = filter_pmc_for_high_acuity(ds, config)
    print(f"  Total matched: {len(matched)}")

    # Per-condition counts
    counts = Counter(m["condition"] for m in matched)
    print("\nMatches per condition:")
    for cond, n in counts.most_common():
        print(f"  {cond:30s} {n:>6d}")

    # Sample 2 cases per condition for sanity-checking
    print("\n" + "=" * 60)
    print("  Random samples per condition (manual sanity check)")
    print("=" * 60)
    by_cond = {}
    for m in matched:
        by_cond.setdefault(m["condition"], []).append(m)
    for cond in counts:
        samples = random.sample(by_cond[cond], min(2, len(by_cond[cond])))
        print(f"\n--- {cond} ({len(by_cond[cond])} total) ---")
        for s in samples:
            snippet = s["description"][:400]
            print(f"\n  [{s['_id']}] matched on '{s['matched_term']}':")
            print(f"  {snippet}{'...' if len(s['description']) > 400 else ''}")


if __name__ == "__main__":
    main()
