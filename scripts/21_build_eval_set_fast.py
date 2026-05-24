"""
Build a smaller evaluation set (v0.2-fast) for tractable local inference.

Samples down from the locked eval_set_v0.1.jsonl:
  200 common / 200 rare / 200 high-acuity = 600 cases.

Uses the same seed for reproducibility.
"""
import json
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from src.data.schema import Case, Stratum

SEED = 42
PER_STRATUM = 200
SRC = Path("data/processed/eval_set_v0.1.jsonl")
OUT = Path("data/processed/eval_set_v0.2_fast.jsonl")
META = Path("data/processed/eval_set_v0.2_fast.meta.json")


def main():
    rng = random.Random(SEED)
    by_stratum = defaultdict(list)
    with open(SRC) as f:
        for line in f:
            c = Case.from_dict(json.loads(line))
            by_stratum[c.stratum].append(c)

    picked = []
    counts = {}
    for stratum in [Stratum.COMMON, Stratum.RARE, Stratum.HIGH_ACUITY]:
        pool = by_stratum[stratum]
        take = min(PER_STRATUM, len(pool))
        chosen = rng.sample(pool, take)
        picked.extend(chosen)
        counts[stratum.value] = take

    rng.shuffle(picked)

    with open(OUT, "w") as f:
        for c in picked:
            f.write(json.dumps(c.to_dict()) + "\n")

    meta = {
        "eval_set_version": "v0.2_fast",
        "derived_from": str(SRC),
        "seed": SEED,
        "per_stratum_target": PER_STRATUM,
        "counts": counts,
        "total": len(picked),
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "reason": "Trimmed for tractable local inference (1-hour sessions, N=3).",
    }
    with open(META, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Wrote {len(picked)} cases to {OUT}")
    print(f"Counts: {counts}")


if __name__ == "__main__":
    main()
