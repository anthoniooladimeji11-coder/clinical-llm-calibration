"""
Explore the structure of PMC-Patients via the NCBI/Open-Patients mirror.
This is an NCBI-published reformatting that includes PMC-Patients notes
alongside USMLE notes, with a clean structure.
"""
from datasets import load_dataset

print("Loading NCBI/Open-Patients...")
ds = load_dataset(
    "ncbi/Open-Patients",
    split="train",
)

print(f"\nTotal cases: {len(ds)}")
print(f"Columns: {ds.column_names}")

# Show the first PMC patient note we find (skip the USMLE ones)
print(f"\nFirst few examples (truncated to 400 chars):")
shown = 0
for i in range(len(ds)):
    ex = ds[i]
    case_id = str(ex.get("_id", ""))
    if not case_id.startswith("pmc-"):
        continue
    print(f"\n  --- Example {i} ({case_id}) ---")
    for k, v in ex.items():
        s = str(v)
        print(f"  {k}: {s[:400]}{'...' if len(s) > 400 else ''}")
    shown += 1
    if shown >= 2:
        break
