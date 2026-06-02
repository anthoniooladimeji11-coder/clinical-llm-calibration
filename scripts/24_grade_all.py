"""
Bulk grader: grade every (case, model) primary answer in the cache and
save verdicts to disk.

For each of the 4 models, walk all 300 cases, run the grader, write a
JSONL row per (case, model). The grader uses cached judge calls where
available and writes new ones to the cache.

Output:
  results/grading_v0.1.jsonl
  results/grading_v0.1.meta.json
"""
import json
import subprocess
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.data.schema import Case, Stratum, CaseFormat
from src.models.cache import ResponseCache, DEFAULT_CACHE_PATH
from src.models.run_case import run_case
from src.grading.grader import grade_case_for_model

MODELS = ["llama-3.1-8b", "qwen2.5-7b", "gemma2-9b", "medgemma-4b"]
EVAL = Path("data/processed/eval_set_v0.3_fast.jsonl")
OUT = Path("results/grading_v0.1.jsonl")
META = Path("results/grading_v0.1.meta.json")


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def main():
    cache = ResponseCache(DEFAULT_CACHE_PATH)

    cases = []
    with open(EVAL) as f:
        for line in f:
            cases.append(Case.from_dict(json.loads(line)))

    total_runs = len(cases) * len(MODELS)
    print(f"Bulk grading: {len(cases)} cases x {len(MODELS)} models "
          f"= {total_runs:,} (case, model) results\n")

    rows = []
    start = time.time()
    stats = defaultdict(lambda: defaultdict(lambda: {"n": 0, "correct": 0}))

    for mi, model_name in enumerate(MODELS, 1):
        print(f">>> MODEL {mi}/{len(MODELS)}: {model_name}")
        for ci, case in enumerate(cases, 1):
            try:
                result = run_case(case, model_name, cache)
                p = result.primary.parsed
                grade = grade_case_for_model(
                    case,
                    primary_answer_letter=p.answer_letter,
                    primary_answer_diagnosis=p.diagnosis,
                    model_under_test=model_name,
                    cache=cache,
                )
                ans = p.answer_letter if case.format == CaseFormat.MULTIPLE_CHOICE else p.diagnosis
                row = {
                    "case_id": case.case_id,
                    "stratum": case.stratum.value,
                    "format": case.format.value,
                    "model": model_name,
                    "ground_truth": case.ground_truth_text,
                    "model_answer": ans,
                    "model_confidence": p.confidence,
                    "answer_parse_ok": p.answer_parse_ok,
                    "confidence_parse_ok": p.confidence_parse_ok,
                    "correct": grade.correct,
                    "grade_method": grade.method,
                    "judge_model": grade.judge_model,
                    "judge_verdict": grade.judge_verdict,
                    "judge_reason": grade.judge_reason,
                }
                rows.append(row)
                stats[model_name][case.stratum.value]["n"] += 1
                if grade.correct:
                    stats[model_name][case.stratum.value]["correct"] += 1
            except KeyboardInterrupt:
                print("\nInterrupted. Partial results not yet saved.")
                raise
            except Exception as e:
                print(f"  [FAIL] {case.case_id} / {model_name}: "
                      f"{str(e)[:120]}")

            if ci % 50 == 0:
                elapsed = time.time() - start
                done_total = (mi - 1) * len(cases) + ci
                rate = done_total / elapsed if elapsed > 0 else 0
                remaining = total_runs - done_total
                eta = timedelta(seconds=int(remaining / rate)) if rate > 0 else "?"
                print(f"  {model_name}: case {ci}/{len(cases)}  "
                      f"| {done_total}/{total_runs} total  | ETA {eta}")

    # Write outputs
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    # Summary
    print(f"\nWrote {len(rows)} graded results to {OUT}")
    print("\n--- Accuracy per (model, stratum) ---")
    print(f"  {'model':14s} {'stratum':14s} {'n':>4s} {'correct':>8s} {'acc':>7s}")
    summary = {}
    for model_name in MODELS:
        summary[model_name] = {}
        for stratum in ["common", "rare", "high_acuity"]:
            s = stats[model_name][stratum]
            acc = (s["correct"] / s["n"]) if s["n"] else 0.0
            print(f"  {model_name:14s} {stratum:14s} {s['n']:>4d} "
                  f"{s['correct']:>8d} {acc:>7.1%}")
            summary[model_name][stratum] = {
                "n": s["n"], "correct": s["correct"], "accuracy": acc,
            }

    meta = {
        "grading_version": "v0.1",
        "eval_set": str(EVAL),
        "models": MODELS,
        "total_results": len(rows),
        "summary": summary,
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "notes": "Bulk grading with cross-judges (Gemma2 9B for non-Gemma2 models; Llama 3.1 8B for Gemma2). Noise filter and high-acuity-specific judge prompt active.",
    }
    with open(META, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"\nMetadata written to {META}")


if __name__ == "__main__":
    main()
