"""
Quick test of the grader against 3 cached case-model results per
stratum, just to confirm it runs end-to-end before bulk grading.
"""
import json
import random
from pathlib import Path

from src.data.schema import Case, Stratum, CaseFormat
from src.models.cache import ResponseCache, DEFAULT_CACHE_PATH
from src.models.run_case import run_case
from src.grading.grader import grade_case_for_model

cache = ResponseCache(DEFAULT_CACHE_PATH)
EVAL = Path("data/processed/eval_set_v0.3_fast.jsonl")

cases = []
with open(EVAL) as f:
    for line in f:
        cases.append(Case.from_dict(json.loads(line)))

by_stratum = {s: [c for c in cases if c.stratum == s] for s in Stratum}
rng = random.Random(7)
sample = []
for s in [Stratum.COMMON, Stratum.RARE, Stratum.HIGH_ACUITY]:
    sample.extend(rng.sample(by_stratum[s], 3))

MODELS = ["llama-3.1-8b", "qwen2.5-7b", "gemma2-9b", "medgemma-4b"]
print(f"Grading {len(sample)} cases x {len(MODELS)} models = "
      f"{len(sample) * len(MODELS)} results\n")

for case in sample:
    print(f"--- {case.case_id} [{case.stratum.value}] ---")
    truth = case.ground_truth_text
    print(f"    Truth: {truth[:80]}{'...' if len(truth) > 80 else ''}")
    for model_name in MODELS:
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
        ans_show = str(ans)[:50] if ans else "[NO ANSWER]"
        flag = "OK " if grade.correct else "BAD"
        extra = ""
        if grade.method == "llm_judge":
            extra = f" (judge={grade.judge_model}, verdict={grade.judge_verdict})"
        print(f"    [{flag}] {model_name:14s} {ans_show!r}{extra}")
    print()
