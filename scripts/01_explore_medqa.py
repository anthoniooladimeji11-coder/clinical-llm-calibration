"""
Explore the structure of MedQA.
Using the GBaker/MedQA-USMLE-4-options mirror — cleaner Parquet format,
same underlying questions as bigbio/med_qa English split.
"""
from datasets import load_dataset

print("Loading MedQA (GBaker mirror, 4-option format)...")
ds = load_dataset(
    "GBaker/MedQA-USMLE-4-options",
    split="train",
)

print(f"\nTotal examples in train split: {len(ds)}")
print(f"Columns: {ds.column_names}")
print(f"\nFirst example (each field truncated to 400 chars):")
ex = ds[0]
for k, v in ex.items():
    s = str(v)
    print(f"\n  {k}:")
    print(f"    {s[:400]}{'...' if len(s) > 400 else ''}")

print(f"\n\nSecond example for comparison:")
ex2 = ds[1]
for k, v in ex2.items():
    s = str(v)
    print(f"\n  {k}:")
    print(f"    {s[:400]}{'...' if len(s) > 400 else ''}")
