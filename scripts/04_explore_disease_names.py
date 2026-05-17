"""
Load phenotype.hpoa and build a lookup from disease code
(OMIM:NNN, ORPHA:NNN, DECIPHER:NNN) to disease name.

Then verify the lookup on the RareBench RAMEDIS example we saw earlier:
  OMIM:251000 -> ???
  ORPHA:27    -> ???
"""
from pathlib import Path

hpoa_path = Path("data/raw/hpo/phenotype.hpoa")

print(f"Loading {hpoa_path}...")

disease_lookup = {}

with open(hpoa_path) as f:
    for line in f:
        if line.startswith("#"):
            continue
        # Skip the header
        if line.startswith("database_id"):
            continue
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 2:
            continue
        code = parts[0].strip()
        name = parts[1].strip()
        if code and name:
            # phenotype.hpoa has one row per (disease, phenotype) pair,
            # so each disease appears many times. We only need the first.
            if code not in disease_lookup:
                disease_lookup[code] = name

# Summary by source
sources = {}
for code in disease_lookup:
    prefix = code.split(":")[0]
    sources[prefix] = sources.get(prefix, 0) + 1

print(f"\nTotal unique diseases: {len(disease_lookup)}")
print(f"By source:")
for src, n in sorted(sources.items()):
    print(f"  {src}: {n}")

# Test on the RareBench RAMEDIS first example
print("\nTest lookups (RareBench RAMEDIS example 0):")
test_codes = ["OMIM:251000", "ORPHA:27", "CCRD:71"]
for code in test_codes:
    name = disease_lookup.get(code, "[NOT FOUND]")
    print(f"  {code:18s}  ->  {name}")
