"""
Build the locked evaluation set.

Pipeline:
  1. Load all cases via unified loaders.
  2. Common stratum: exclude pediatric vignettes; sample 800.
  3. Rare stratum: quality filter (>=3 phenotypes, no label leakage);
     sample 600.
  4. High-acuity stratum: within-stratum balanced sample (<=70/condition).
  5. Save to data/processed/eval_set_v0.1.jsonl + a .meta.json sidecar.

This runs ONCE. Every downstream piece of code reads the JSONL.
"""
import json
import random
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src.data.loaders import (
    load_medqa_cases,
    load_rarebench_cases,
    load_pmc_cases,
)
from src.data.filters import (
    exclude_pediatric,
    apply_rare_quality_filter,
)
from src.data.schema import Stratum


EVAL_SET_VERSION = "v0.1"
RANDOM_SEED = 42
COMMON_TARGET_N = 800
RARE_TARGET_N = 600
HIGH_ACUITY_MAX_PER_CONDITION = 70

OUTPUT_DIR = Path("data/processed")
JSONL_PATH = OUTPUT_DIR / f"eval_set_{EVAL_SET_VERSION}.jsonl"
META_PATH = OUTPUT_DIR / f"eval_set_{EVAL_SET_VERSION}.meta.json"


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def sample_common(rng: random.Random) -> tuple[list, dict]:
    print("\n--- Common stratum (MedQA) ---")
    raw = load_medqa_cases()
    print(f"  Loaded:                 {len(raw):>6,}")
    after_ped = exclude_pediatric(raw)
    n_ped_dropped = len(raw) - len(after_ped)
    print(f"  After pediatric filter: {len(after_ped):>6,} "
          f"(dropped {n_ped_dropped})")
    if len(after_ped) < COMMON_TARGET_N:
        raise RuntimeError(
            f"Not enough common cases after filter: "
            f"{len(after_ped)} < {COMMON_TARGET_N}"
        )
    sampled = rng.sample(after_ped, COMMON_TARGET_N)
    print(f"  Sampled:                {len(sampled):>6,}")
    return sampled, {
        "raw_n": len(raw),
        "after_pediatric_filter_n": len(after_ped),
        "n_pediatric_dropped": n_ped_dropped,
        "sampled_n": len(sampled),
    }


def sample_rare(rng: random.Random) -> tuple[list, dict]:
    print("\n--- Rare stratum (RareBench) ---")
    raw = load_rarebench_cases()
    print(f"  Loaded:                 {len(raw):>6,}")
    filtered = apply_rare_quality_filter(raw)
    print(f"  After quality filter:   {len(filtered):>6,}")
    if len(filtered) < RARE_TARGET_N:
        print(f"  WARNING: only {len(filtered)} cases after filter, "
              f"target was {RARE_TARGET_N}.")
        sampled = list(filtered)  # take everything
    else:
        sampled = rng.sample(filtered, RARE_TARGET_N)
    rng.shuffle(sampled)
    print(f"  Sampled:                {len(sampled):>6,}")
    return sampled, {
        "raw_n": len(raw),
        "after_quality_filter_n": len(filtered),
        "n_dropped_by_quality_filter": len(raw) - len(filtered),
        "sampled_n": len(sampled),
    }


def sample_high_acuity(rng: random.Random) -> tuple[list, dict]:
    print("\n--- High-acuity stratum (PMC-Patients) ---")
    raw = load_pmc_cases()
    print(f"  Loaded:                 {len(raw):>6,}")
    by_condition = {}
    for c in raw:
        by_condition.setdefault(c.condition_tag, []).append(c)
    sampled = []
    per_condition_n = {}
    for cond, cond_cases in by_condition.items():
        take = min(HIGH_ACUITY_MAX_PER_CONDITION, len(cond_cases))
        chosen = rng.sample(cond_cases, take)
        sampled.extend(chosen)
        per_condition_n[cond] = take
    rng.shuffle(sampled)
    print(f"  Balanced sample:        {len(sampled):>6,}")
    for cond, n in sorted(per_condition_n.items(),
                          key=lambda x: -x[1]):
        print(f"    {cond:30s} {n:>4d}")
    return sampled, {
        "raw_n": len(raw),
        "max_per_condition": HIGH_ACUITY_MAX_PER_CONDITION,
        "per_condition_sampled_n": per_condition_n,
        "sampled_n": len(sampled),
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(RANDOM_SEED)

    common_cases, common_meta = sample_common(rng)
    rare_cases, rare_meta = sample_rare(rng)
    high_cases, high_meta = sample_high_acuity(rng)

    all_cases = common_cases + rare_cases + high_cases
    rng.shuffle(all_cases)
    print(f"\n=== Final evaluation set ===")
    print(f"  Total cases:            {len(all_cases):>6,}")
    print(f"    Common:               {len(common_cases):>6,}")
    print(f"    Rare:                 {len(rare_cases):>6,}")
    print(f"    High-acuity:          {len(high_cases):>6,}")

    print(f"\nWriting JSONL to {JSONL_PATH} ...")
    with open(JSONL_PATH, "w") as f:
        for c in all_cases:
            f.write(json.dumps(c.to_dict()) + "\n")

    metadata = {
        "eval_set_version": EVAL_SET_VERSION,
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "random_seed": RANDOM_SEED,
        "targets": {
            "common": COMMON_TARGET_N,
            "rare": RARE_TARGET_N,
            "high_acuity_max_per_condition": HIGH_ACUITY_MAX_PER_CONDITION,
        },
        "common": common_meta,
        "rare": rare_meta,
        "high_acuity": high_meta,
        "totals": {
            "common": len(common_cases),
            "rare": len(rare_cases),
            "high_acuity": len(high_cases),
            "all": len(all_cases),
        },
        "output_jsonl": str(JSONL_PATH),
    }
    print(f"Writing metadata to {META_PATH} ...")
    with open(META_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    print("\nDone.")


if __name__ == "__main__":
    main()
