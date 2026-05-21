"""
Test the unified call_model() interface against all four models.
Confirms each returns text (no logprobs — we use sampling-based UQ).
"""
from src.models.inference import call_model

MODELS = ["llama-3.3-70b", "llama-3.1-8b", "qwen3-32b", "biomistral-7b"]

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Name the largest organ in the human body in one word."},
]

for model_name in MODELS:
    print(f"\n{'=' * 60}\n  {model_name}\n{'=' * 60}")
    try:
        resp = call_model(
            model_name,
            messages,
            temperature=0.0,
            max_tokens=50,
            seed=42,
        )
        print(f"  provider:      {resp.provider}")
        print(f"  finish_reason: {resp.finish_reason}")
        print(f"  text:          {resp.text[:150]!r}")
    except Exception as e:
        print(f"  FAILED: {e}")
