"""
Verify Groq API access for the final lineup.
- Loads GROQ_API_KEY from .env
- Makes one test call to each Groq model in our lineup
"""
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise SystemExit("GROQ_API_KEY not found in environment / .env")

client = Groq(api_key=api_key)

lineup = {
    "llama-3.3-70b": "llama-3.3-70b-versatile",
    "llama-3.1-8b": "llama-3.1-8b-instant",
    "qwen3-32b": "qwen/qwen3-32b",
}

print("=" * 60)
print("  Test call to each Groq lineup model")
print("=" * 60)
test_prompt = "Reply with exactly one word: working"
all_ok = True
for nickname, model_id in lineup.items():
    print(f"\n  {nickname} ({model_id}):")
    try:
        resp = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": test_prompt}],
            max_tokens=20,
            temperature=0,
        )
        print(f"    Response: {resp.choices[0].message.content!r}")
    except Exception as e:
        print(f"    FAILED: {e}")
        all_ok = False

print("\n" + "=" * 60)
print(f"  All three Groq models working: {all_ok}")
print("=" * 60)
