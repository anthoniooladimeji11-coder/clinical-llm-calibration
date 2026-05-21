"""
Pilot inference run: a small balanced sample across all strata and all
models, written to the REAL cache so the calls count toward the full run.

Purpose: catch format/parsing problems on ~20 cases before committing to
the multi-day full run. Reports parse-success rates and sample outputs.

Output:
  results/pilot_results.jsonl   (one row per case-model result)
"""
import json
import random
from collections import defaultdict
from pathlib import Path

from src.data.schema import Case, Stratum
from src.models.cache import ResponseCache, DEFAULT_CACHE_PATH
from src.models.run_case import run_case

CASES_PER_STRATUM = 7
MODELS = ["llama-3.1-8b", "medgemma-4b"]
EVAL_SET = Path("data/processed/eval_set_v0.1.jsonl")
OUT_PATH = Path("results/pilot_results.jsonl")
SEED = 42


def load_eval_cases() -> list[Case]:
    cases = []
    with open(EVAL_SET) as f:
        for line in f:
            cases.append(Case.from_dict(json.loads(line)))
    return cases


def pick_pilot_cases(cases: list[Case], rng: random.Random) -> list[Case]:
    by_stratum = defaultdict(list)
    for c in cases:
        by_stratum[c.stratum].append(c)
    picked = []
    for stratum in [Stratum.COMMON, Stratum.RARE, Stratum.HIGH_ACUITY]:
        pool = by_stratum[stratum]
        picked.extend(rng.sample(pool, min(CASES_PER_STRATUM, len(pool))))
    return picked


def main():
    rng = random.Random(SEED)
    cache = ResponseCache(DEFAULT_CACHE_PATH)

    all_cases = load_eval_cases()
    pilot_cases = pick_pilot_cases(all_cases, rng)
    print(f"Pilot: {len(pilot_cases)} cases x {len(MODELS)} models "
          f"= {len(pilot_cases) * len(MODELS)} case-model runs "
          f"({len(pilot_cases) * len(MODELS) * 6} total calls)\n")

    # Track parse stats: model -> stratum -> counters
    stats = defaultdict(lambda: defaultdict(lambda: {
        "n": 0, "answer_ok": 0, "conf_ok": 0, "fallback": 0,
    }))

    rows = []
    for ci, case in enumerate(pilot_cases):
        print(f"[{ci + 1}/{len(pilot_cases)}] {case.case_id} "
              f"({case.stratum.value})")
        for model_name in MODELS:
            result = run_case(case, model_name, cache)
            p = result.primary.parsed
            s = stats[model_name][case.stratum.value]
            s["n"] += 1
            if p.answer_parse_ok:
                s["answer_ok"] += 1
            if p.confidence_parse_ok:
                s["conf_ok"] += 1
            if p.used_fallback:
                s["fallback"] += 1

            answer = p.answer_letter if result.is_multiple_choice else p.diagnosis
            sample_answers = [
                (sm.parsed.answer_letter if result.is_multiple_choice
                 else sm.parsed.diagnosis)
                for sm in result.samples
            ]
            sample_confs = [sm.parsed.confidence for sm in result.samples]

            rows.append({
                "case_id": case.case_id,
                "stratum": case.stratum.value,
                "model": model_name,
                "ground_truth": case.ground_truth_text,
                "primary_answer": answer,
                "primary_confidence": p.confidence,
                "answer_parse_ok": p.answer_parse_ok,
                "confidence_parse_ok": p.confidence_parse_ok,
                "used_fallback": p.used_fallback,
                "sample_answers": sample_answers,
                "sample_confidences": sample_confs,
            })
            mark = "OK" if p.answer_parse_ok else "FAIL"
            print(f"    {model_name:16s} [{mark}] "
                  f"answer={str(answer)[:40]!r} conf={p.confidence}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"\nWrote {len(rows)} rows to {OUT_PATH}")

    # --- Parse-success summary ---
    print("\n" + "=" * 70)
    print("  PARSE-SUCCESS SUMMARY (primary answer)")
    print("=" * 70)
    print(f"  {'model':16s} {'stratum':14s} {'n':>3s} "
          f"{'ans_ok':>7s} {'conf_ok':>8s} {'fallback':>9s}")
    for model_name in MODELS:
        for stratum in ["common", "rare", "high_acuity"]:
            s = stats[model_name][stratum]
            if s["n"] == 0:
                continue
            print(f"  {model_name:16s} {stratum:14s} {s['n']:>3d} "
                  f"{s['answer_ok']:>7d} {s['conf_ok']:>8d} "
                  f"{s['fallback']:>9d}")


if __name__ == "__main__":
    main()
