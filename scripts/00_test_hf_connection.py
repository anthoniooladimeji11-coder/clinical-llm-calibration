"""
Sanity check: explore all RareBench splits to find which contain
readable case text vs. just codes.
"""
from datasets import load_dataset

splits_to_try = ["RAMEDIS", "MME", "HMS", "LIRICAL", "PUMCH"]

for split_name in splits_to_try:
    print(f"\n{'=' * 60}")
    print(f"  RareBench / {split_name}")
    print('=' * 60)
    try:
        ds = load_dataset(
            "chenxz/RareBench",
            split_name,
            split="test",
            trust_remote_code=True,
        )
        print(f"  Loaded {len(ds)} examples")
        print(f"  Columns: {ds.column_names}")
        print(f"\n  First example (each field truncated to 300 chars):")
        ex = ds[0]
        for k, v in ex.items():
            s = str(v)
            print(f"    {k}: {s[:300]}{'...' if len(s) > 300 else ''}")
    except Exception as e:
        print(f"  FAILED: {e}")
