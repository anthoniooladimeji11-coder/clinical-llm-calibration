"""
Explore the structure of MedMCQA.
Indian medical entrance exam questions, used as the second source
for the common-stratum eval set.
"""
from datasets import load_dataset

print("Loading MedMCQA (validation split)...")
ds = load_dataset(
    "openlifescienceai/medmcqa",
    split="validation",
)

print(f"\nTotal examples in validation split: {len(ds)}")
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
