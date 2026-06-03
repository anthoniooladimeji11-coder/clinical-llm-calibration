"""
For each row in results/grading_v0.1.jsonl, pull the 3 sampled answers
from the cache, compute UQ signals, and write to results/grading_with_uq_v0.1.jsonl.

UQ signals attached per row:
  - verbalized_confidence  (already present, re-emitted for convenience)
  - self_consistency_variance
  - semantic_entropy
  - n_usable_samples
  - sample_answers_normalized
"""
import json
from pathlib import Path

from src.data.schema import Case, CaseFormat
from src.models.cache import ResponseCache, DEFAULT_CACHE_PATH
from src.models.run_case import run_case
from src.calibration.uq_signals import compute_uq_from_samples


GRADING = Path("results/grading_v0.1.jsonl")
EVAL = Path("data/processed/eval_set_v0.3_fast.jsonl")
OUT = Path("results/grading_with_uq_v0.1.jsonl")


def main():
    cache = ResponseCache(DEFAULT_CACHE_PATH)

    # Build case lookup
    cases_by_id = {}
    with open(EVAL) as f:
        for line in f:
            c = Case.from_dict(json.loads(line))
            cases_by_id[c.case_id] = c

    rows = []
    with open(GRADING) as f:
        for line in f:
            rows.append(json.loads(line))

    print(f"Loaded {len(rows)} graded rows. Attaching UQ signals...\n")

    out_rows = []
    for i, r in enumerate(rows, 1):
        case = cases_by_id[r["case_id"]]
        is_mc = case.format == CaseFormat.MULTIPLE_CHOICE

        # Pull the sampled answers via run_case (everything cached, instant)
        result = run_case(case, r["model"], cache)
        if is_mc:
            sample_answers = [s.parsed.answer_letter for s in result.samples]
        else:
            sample_answers = [s.parsed.diagnosis for s in result.samples]

        uq = compute_uq_from_samples(is_mc, sample_answers)

        new_row = dict(r)
        new_row.update({
            "n_usable_samples": uq.n_samples,
            "self_consistency_variance": uq.self_consistency_variance,
            "semantic_entropy": uq.semantic_entropy,
            "sample_answers_normalized": uq.sample_answers_normalized,
        })
        out_rows.append(new_row)

        if i % 200 == 0:
            print(f"  ...{i}/{len(rows)}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        for r in out_rows:
            f.write(json.dumps(r) + "\n")

    print(f"\nWrote {len(out_rows)} rows to {OUT}")

    # Quick sanity stats per stratum/model
    print("\nMean self-consistency variance per (model, stratum):")
    print(f"  {'model':14s} {'stratum':12s} {'n':>4s} {'var':>7s} {'ent':>7s}")
    by = {}
    for r in out_rows:
        key = (r["model"], r["stratum"])
        by.setdefault(key, []).append(r)
    for (m, s), rs in sorted(by.items()):
        var_vals = [x["self_consistency_variance"] for x in rs
                    if x["self_consistency_variance"] is not None]
        ent_vals = [x["semantic_entropy"] for x in rs
                    if x["semantic_entropy"] is not None]
        var_mean = sum(var_vals) / len(var_vals) if var_vals else float("nan")
        ent_mean = sum(ent_vals) / len(ent_vals) if ent_vals else float("nan")
        print(f"  {m:14s} {s:12s} {len(rs):>4d} "
              f"{var_mean:>7.3f} {ent_mean:>7.3f}")


if __name__ == "__main__":
    main()
