"""
End-to-end test of the RareBench converter.
Loads a few cases from each RareBench split, converts them, and prints
the resulting vignettes alongside the ground-truth diagnoses.
"""
from pathlib import Path

from datasets import load_dataset

from src.data.rarebench import (
    load_hpo_phenotype_lookup,
    load_disease_name_lookup,
    convert_case,
)

print("Loading lookups...")
hp_lookup = load_hpo_phenotype_lookup(Path("data/raw/hpo/hp.json"))
disease_lookup = load_disease_name_lookup(Path("data/raw/hpo/phenotype.hpoa"))
print(f"  HPO terms:      {len(hp_lookup)}")
print(f"  Disease names:  {len(disease_lookup)}")

splits = ["RAMEDIS", "MME", "HMS", "LIRICAL"]
for split_name in splits:
    print(f"\n{'=' * 60}")
    print(f"  RareBench / {split_name}  (first 2 converted cases)")
    print('=' * 60)
    ds = load_dataset(
        "chenxz/RareBench",
        split_name,
        split="test",
        trust_remote_code=True,
    )
    shown = 0
    skipped = 0
    for i in range(len(ds)):
        case = convert_case(ds[i], hp_lookup, disease_lookup)
        if case is None:
            skipped += 1
            continue
        print(f"\n  Case {i}:")
        print(f"    Vignette: {case['vignette'][:300]}"
              f"{'...' if len(case['vignette']) > 300 else ''}")
        print(f"    True Dx:  {case['ground_truth_dx']}")
        print(f"    N phenotypes: {case['n_phenotypes']}")
        shown += 1
        if shown >= 2:
            break

    # Summary count for the whole split
    total_convertible = sum(
        1 for i in range(len(ds))
        if convert_case(ds[i], hp_lookup, disease_lookup) is not None
    )
    print(f"\n  Summary for {split_name}: "
          f"{total_convertible}/{len(ds)} cases convert successfully.")
