"""
Test the response parser against representative outputs:
strict format, Qwen think-tags, loose format, and parse failure.
"""
from src.models.parser import parse_response

# --- Multiple choice cases ---
mc_examples = [
    ("strict",
     "The patient has dysuria in pregnancy.\nANSWER: D\nCONFIDENCE: 85"),
    ("qwen-think",
     "<think>\nLet me reason. Pregnancy + UTI means nitrofurantoin.\n</think>\n"
     "Nitrofurantoin is safe in pregnancy.\nANSWER: D\nCONFIDENCE: 90"),
    ("loose",
     "I think the answer is (B) because of the presentation. "
     "My confidence is about 70%."),
    ("failure",
     "This is a complex case and I cannot determine the answer."),
]

print("=" * 60)
print("  MULTIPLE CHOICE")
print("=" * 60)
for label, text in mc_examples:
    p = parse_response(text, is_multiple_choice=True)
    print(f"\n[{label}]")
    print(f"  letter={p.answer_letter}  conf={p.confidence}  "
          f"ans_ok={p.answer_parse_ok}  conf_ok={p.confidence_parse_ok}  "
          f"fallback={p.used_fallback}")

# --- Open-ended cases ---
oe_examples = [
    ("strict",
     "Reasoning about the phenotypes.\n"
     "DIAGNOSIS: Methylmalonic acidemia\nCONFIDENCE: 60"),
    ("qwen-think",
     "<think>\nPhenotypes suggest an organic acidemia.\n</think>\n"
     "DIAGNOSIS: Glutaric acidemia type I\nCONFIDENCE: 55"),
    ("loose",
     "Given the features, the most likely diagnosis is acute pancreatitis. "
     "I'd estimate my probability at 75%."),
    ("failure",
     "There are many possibilities here and the picture is unclear."),
]

print("\n" + "=" * 60)
print("  OPEN ENDED")
print("=" * 60)
for label, text in oe_examples:
    p = parse_response(text, is_multiple_choice=False)
    print(f"\n[{label}]")
    print(f"  dx={p.diagnosis!r}  conf={p.confidence}  "
          f"ans_ok={p.answer_parse_ok}  conf_ok={p.confidence_parse_ok}  "
          f"fallback={p.used_fallback}")
