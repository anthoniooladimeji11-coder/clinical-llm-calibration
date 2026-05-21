"""
Diagnose why BioMistral returns empty output.
Try several prompt configurations to isolate the cause.
"""
from src.models.inference import call_model

vignette = (
    "A 23-year-old pregnant woman at 22 weeks gestation presents with "
    "burning upon urination for 1 day. No costovertebral angle tenderness. "
    "Which is the best treatment? A) Ampicillin B) Ceftriaxone "
    "C) Doxycycline D) Nitrofurantoin"
)

tests = [
    ("plain user msg, no system",
     [{"role": "user", "content": vignette + "\n\nAnswer:"}]),
    ("user msg with system",
     [{"role": "system", "content": "You are a physician."},
      {"role": "user", "content": vignette + "\n\nAnswer:"}]),
    ("just the question, very short",
     [{"role": "user", "content": "What antibiotic treats a UTI in pregnancy? Answer in one sentence."}]),
]

for label, messages in tests:
    print(f"\n{'=' * 60}\n  {label}\n{'=' * 60}")
    resp = call_model(
        "biomistral-7b", messages,
        temperature=0.0, max_tokens=256, seed=42,
    )
    print(f"  finish_reason: {resp.finish_reason}")
    print(f"  text ({len(resp.text)} chars): {resp.text!r}")
