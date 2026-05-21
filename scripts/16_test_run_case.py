"""
End-to-end test: run ONE case through all four models with full
self-consistency (1 deterministic + 5 sampled calls each).

Uses a temporary cache so it doesn't pollute the real one.
"""
from pathlib import Path

from src.data.loaders import load_medqa_cases
from src.models.cache import ResponseCache
from src.models.run_case import run_case

TEST_CACHE = Path("results/_test_run_case.sqlite")
if TEST_CACHE.exists():
    TEST_CACHE.unlink()
cache = ResponseCache(TEST_CACHE)

# Grab one MedQA case (multiple choice, common stratum)
case = load_medqa_cases()[0]
print(f"Case: {case.case_id} ({case.stratum.value}, {case.format.value})")
print(f"Vignette (truncated): {case.vignette[:150]}...")
print(f"Ground truth: {case.ground_truth_letter} = {case.ground_truth_text}\n")

MODELS = ["llama-3.3-70b", "llama-3.1-8b", "qwen3-32b", "medgemma-4b"]

for model_name in MODELS:
    print(f"{'=' * 60}\n  {model_name}\n{'=' * 60}")
    result = run_case(case, model_name, cache)
    p = result.primary.parsed
    print(f"  PRIMARY: answer={p.answer_letter} conf={p.confidence} "
          f"(ok={p.answer_parse_ok}/{p.confidence_parse_ok})")
    print(f"  SAMPLES:")
    for s in result.samples:
        sp = s.parsed
        print(f"    [{s.sample_index}] answer={sp.answer_letter} "
              f"conf={sp.confidence} fb={sp.used_fallback}")

cache_count = cache.count()
print(f"\nTotal cached calls: {cache_count} "
      f"(expected {len(MODELS)} x 6 = {len(MODELS) * 6})")
TEST_CACHE.unlink()
print("Cleaned up test cache.")
