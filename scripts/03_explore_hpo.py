"""
Load the HPO JSON ontology and verify we can map an HPO code
(e.g. HP:0001522) to its human-readable label (e.g. "Death in childhood").

This is the foundation for converting RareBench code-lists into
clinical-vignette text.
"""
import json
from pathlib import Path

hpo_path = Path("data/raw/hpo/hp.json")

print(f"Loading HPO from {hpo_path}...")
with open(hpo_path) as f:
    hpo = json.load(f)

print(f"\nTop-level keys: {list(hpo.keys())}")

# HPO JSON follows the OBO Graph format. The terms live under
# graphs[0]['nodes']. Each node has an 'id' (a URL like
# http://purl.obolibrary.org/obo/HP_0001522) and a 'lbl' (label).
nodes = hpo['graphs'][0]['nodes']
print(f"\nTotal nodes: {len(nodes)}")
print(f"\nFirst 3 nodes for shape inspection:")
for n in nodes[:3]:
    print(f"  {n}")

# Build a lookup dict: HP:NNNNNNN -> label
print("\nBuilding HP_code -> label lookup...")
hp_lookup = {}
for n in nodes:
    node_id = n.get('id', '')
    label = n.get('lbl', '')
    if 'HP_' in node_id and label:
        # Convert http://purl.obolibrary.org/obo/HP_0001522 -> HP:0001522
        code = node_id.split('/')[-1].replace('_', ':')
        hp_lookup[code] = label

print(f"Built lookup with {len(hp_lookup)} HP terms.")

# Test it on the codes from the RareBench example we saw earlier
print("\nTest lookups (from RareBench RAMEDIS example 0):")
test_codes = ['HP:0001522', 'HP:0001942', 'HP:0003210', 'HP:0003819']
for code in test_codes:
    label = hp_lookup.get(code, "[NOT FOUND]")
    print(f"  {code}  ->  {label}")
