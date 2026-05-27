"""
Build a 300-case evaluation set (v0.3_fast) for fast local inference.
100 common / 100 rare / 100 high-acuity, seed 42, sampled from v0.1.
"""
import json
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from src.data.schema import Case, Stratum

SEED = 42
PER_STRATUM = 100
SRC = Path("data/processed/eval_set_v0.1.jsonl")
OUT = Path("data/processed/eval_set_v0.3_fast.jsonl")
META = Path("data/processed/eval_set_v0.3_fast.meta.json")


def main():
    rng = random.Random(SEED)
    by_stratum = defaultdict(list)
    with open(SRC) as f:
        for line in f:
            c = Case.from_dict(json.loads(line))
            by_stratum[c.stratum].append(c)

    picked, counts = [], {}
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
        "eval_set_version": "v0.3_fast",
        "derived_from": str(SRC),
        "seed": SEED,
        "per_stratum_target": PER_STRATUM,
        "counts": counts,
        "total": len(picked),
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "reason": "Pilot-scale set (300 cases) for tractable local inference.",
    }
    with open(META, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Wrote {len(picked)} cases to {OUT}")
    print(f"Counts: {counts}")


if __name__ == "__main__":
    main()
