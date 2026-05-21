"""
Test whether MedGemma 4B follows our structured prompt where
BioMistral failed. Same case, same prompt format.
"""
from src.data.loaders import load_medqa_cases
from src.models.inference import call_model
from src.models.prompts import build_messages
from src.models.parser import parse_response

case = load_medqa_cases()[0]
messages = build_messages(case)

print(f"Ground truth: {case.ground_truth_letter} = {case.ground_truth_text}\n")
print("MEDGEMMA 4B RAW OUTPUT:")
print("=" * 60)
resp = call_model(
    "medgemma-4b", messages,
    temperature=0.0, max_tokens=1024, seed=42,
)
print(resp.text)
print("=" * 60)

parsed = parse_response(resp.text, is_multiple_choice=True)
print(f"\nPARSED:")
print(f"  answer={parsed.answer_letter}  confidence={parsed.confidence}")
print(f"  answer_ok={parsed.answer_parse_ok}  conf_ok={parsed.confidence_parse_ok}")
print(f"  used_fallback={parsed.used_fallback}")
