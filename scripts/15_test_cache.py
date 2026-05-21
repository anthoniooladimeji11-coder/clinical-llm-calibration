"""
Test the response cache: put, get (hit), get (miss), count, stats.
Uses a temporary cache file so it doesn't touch the real one.
"""
from pathlib import Path

from src.models.cache import ResponseCache

TEST_PATH = Path("results/_test_cache.sqlite")
if TEST_PATH.exists():
    TEST_PATH.unlink()

cache = ResponseCache(TEST_PATH)

messages = [
    {"role": "system", "content": "You are a physician."},
    {"role": "user", "content": "Diagnose this case..."},
]

# Miss before storing
hit = cache.get("llama-3.3-70b", messages, 0.7, 42, 0)
print(f"Before put -> get returns: {hit}  (expected None)")

# Store
cache.put(
    model_name="llama-3.3-70b",
    messages=messages,
    temperature=0.7,
    seed=42,
    sample_index=0,
    case_id="medqa-train-00001",
    text="ANSWER: D\nCONFIDENCE: 85",
    finish_reason="stop",
    provider="groq",
)
print("Stored one response.")

# Hit after storing (same key)
hit = cache.get("llama-3.3-70b", messages, 0.7, 42, 0)
print(f"After put  -> get returns: {hit!r}")

# Miss on a different sample_index
miss = cache.get("llama-3.3-70b", messages, 0.7, 42, 1)
print(f"Different sample_index -> get returns: {miss}  (expected None)")

# Counts and stats
print(f"Total cached: {cache.count()}")
print(f"Stats: {cache.stats()}")

# Clean up
TEST_PATH.unlink()
print("Cleaned up test cache.")
