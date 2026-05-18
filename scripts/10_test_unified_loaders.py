"""
End-to-end test: load every source through the unified Case schema
and report counts plus a sample case from each stratum.
"""
from collections import Counter

from src.data.loaders import (
    load_medqa_cases,
    load_rarebench_cases,
    load_pmc_cases,
)


def show_sample(case, max_vignette_chars=400):
    print(f"  case_id:           {case.case_id}")
    print(f"  source:            {case.source}")
    print(f"  stratum:           {case.stratum.value}")
    print(f"  format:            {case.format.value}")
    v = case.vignette
    print(f"  vignette ({len(v)} chars):")
    print(f"    {v[:max_vignette_chars]}{'...' if len(v) > max_vignette_chars else ''}")
    print(f"  ground_truth_text: {case.ground_truth_text}")
    if case.ground_truth_letter:
        print(f"  ground_truth_letter: {case.ground_truth_letter}")
    if case.options:
        print(f"  options:           {case.options}")
    if case.condition_tag:
        print(f"  condition_tag:     {case.condition_tag}")
    if case.notes:
        print(f"  notes:             {case.notes}")


def main():
    print("=" * 60)
    print("  Loading MedQA")
    print("=" * 60)
    medqa = load_medqa_cases()
    print(f"  Loaded {len(medqa):,} common-stratum cases.")
    print(f"\n  Sample case:")
    show_sample(medqa[0])

    print("\n" + "=" * 60)
    print("  Loading RareBench")
    print("=" * 60)
    rare = load_rarebench_cases()
    print(f"  Loaded {len(rare):,} rare-stratum cases.")
    splits = Counter(c.notes.get("split") for c in rare)
    print(f"  By split: {dict(splits)}")
    print(f"\n  Sample case:")
    show_sample(rare[0])

    print("\n" + "=" * 60)
    print("  Loading PMC-Patients (high-acuity)")
    print("=" * 60)
    pmc = load_pmc_cases()
    print(f"  Loaded {len(pmc):,} high-acuity cases.")
    cond_counts = Counter(c.condition_tag for c in pmc)
    print(f"  By condition:")
    for cond, n in cond_counts.most_common():
        print(f"    {cond:30s} {n:>5d}")
    print(f"\n  Sample case:")
    show_sample(pmc[0])

    print("\n" + "=" * 60)
    print("  Totals")
    print("=" * 60)
    print(f"  Common:       {len(medqa):>6,}")
    print(f"  Rare:         {len(rare):>6,}")
    print(f"  High-acuity:  {len(pmc):>6,}")
    print(f"  ---")
    print(f"  Total cases:  {len(medqa) + len(rare) + len(pmc):>6,}")


if __name__ == "__main__":
    main()
