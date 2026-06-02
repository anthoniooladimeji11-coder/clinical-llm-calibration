"""
Quick sanity check on the UQ math:
- All-same samples -> variance 0, entropy 0
- All-different samples -> variance high, entropy log(n)
- Some agreement, some not -> something in between
"""
import math
from src.calibration.uq_signals import compute_uq_from_samples

cases = [
    ("MC all agree", True, ["A", "A", "A"]),
    ("MC all disagree", True, ["A", "B", "C"]),
    ("MC 2v1 split", True, ["B", "B", "A"]),
    ("MC with one None", True, ["A", None, "A"]),
    ("OE all same dx", False, ["Phenylketonuria", "Phenylketonuria (PKU)", "PKU"]),
    ("OE all different", False, ["DKA", "Sepsis", "STEMI"]),
    ("OE all None", False, [None, None, None]),
]

for label, is_mc, samples in cases:
    u = compute_uq_from_samples(is_mc, samples)
    print(f"{label}")
    print(f"  n={u.n_samples}  "
          f"variance={u.self_consistency_variance}  "
          f"entropy={u.semantic_entropy}")
    print(f"  normalized={u.sample_answers_normalized}\n")
