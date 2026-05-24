"""
Full inference run over the locked evaluation set.

Fully resumable: every model call is cached to SQLite the moment it
completes. If the run is interrupted (sleep, crash, Ctrl+C, close),
just run this script again — it skips everything already cached and
continues from where it stopped.

Crash-tolerant: a failure on one case-model is logged and skipped, not
fatal. Re-running picks up the skipped ones.

Usage:
  python scripts/20_run_inference.py
  # or, to keep the Mac awake for the whole run:
  caffeinate -i python scripts/20_run_inference.py

Models run are whichever are listed in MODELS below AND currently
available in Ollama. Missing models are skipped with a warning, so you
can start on the 2 ready models and add the others later.
"""
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

from src.data.schema import Case
from src.models.cache import ResponseCache, DEFAULT_CACHE_PATH
from src.models.run_case import run_case, N_SAMPLES
from src.models.inference import get_model_spec

# All four eventually; only those present in Ollama will actually run.
MODELS = ["llama-3.1-8b", "qwen2.5-7b", "gemma2-9b", "medgemma-4b"]

EVAL_SET = Path("data/processed/eval_set_v0.2_fast.jsonl")
PROGRESS_LOG = Path("results/inference_progress.log")
FAILURE_LOG = Path("results/inference_failures.jsonl")
CALLS_PER_CASE = 1 + N_SAMPLES  # 1 deterministic + N sampled


def load_eval_cases() -> list[Case]:
    cases = []
    with open(EVAL_SET) as f:
        for line in f:
            cases.append(Case.from_dict(json.loads(line)))
    return cases


def ollama_available_models() -> set:
    """Return the set of model tags currently downloaded in Ollama."""
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=10)
        r.raise_for_status()
        data = r.json()
        return {m["name"] for m in data.get("models", [])}
    except Exception:
        return set()


def model_is_ready(model_name: str, ollama_models: set) -> bool:
    spec = get_model_spec(model_name)
    if spec["provider"] != "ollama":
        return True  # non-ollama models handled elsewhere
    target = spec["ollama_model_id"]
    # Ollama tags may or may not include ":latest"
    return any(
        target == m or target == m.split(":")[0] or m.startswith(target)
        for m in ollama_models
    )


def log(msg: str):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line)
    PROGRESS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_LOG, "a") as f:
        f.write(line + "\n")


def main():
    cache = ResponseCache(DEFAULT_CACHE_PATH)
    cases = load_eval_cases()

    ollama_models = ollama_available_models()
    active_models = [m for m in MODELS if model_is_ready(m, ollama_models)]
    skipped_models = [m for m in MODELS if m not in active_models]

    log("=" * 60)
    log("INFERENCE RUN START")
    log(f"  Eval cases:      {len(cases):,}")
    log(f"  Models to run:   {active_models}")
    if skipped_models:
        log(f"  Skipped (not downloaded yet): {skipped_models}")
    total_runs = len(cases) * len(active_models)
    log(f"  Case-model runs: {total_runs:,}  "
        f"({total_runs * CALLS_PER_CASE:,} total calls)")
    log("=" * 60)

    start = time.time()
    completed = 0
    failed = 0
    session_calls = 0

    for mi, model_name in enumerate(active_models, 1):
        log(f"\n>>> MODEL {mi}/{len(active_models)}: {model_name}")
        for ci, case in enumerate(cases, 1):
            try:
                # run_case checks cache per call internally
                before = cache.count(model_name)
                run_case(case, model_name, cache)
                after = cache.count(model_name)
                session_calls += (after - before)
                completed += 1
            except KeyboardInterrupt:
                log("\nInterrupted by user (Ctrl+C). "
                    "Progress is cached — re-run to continue.")
                return
            except Exception as e:
                failed += 1
                FAILURE_LOG.parent.mkdir(parents=True, exist_ok=True)
                with open(FAILURE_LOG, "a") as f:
                    f.write(json.dumps({
                        "case_id": case.case_id,
                        "model": model_name,
                        "error": str(e)[:500],
                        "at": datetime.now().isoformat(),
                    }) + "\n")
                log(f"  [FAIL] {case.case_id} / {model_name}: "
                    f"{str(e)[:120]}")

            # Progress every 50 cases
            if ci % 50 == 0:
                elapsed = time.time() - start
                done_total = (mi - 1) * len(cases) + ci
                rate = done_total / elapsed if elapsed > 0 else 0
                remaining = total_runs - done_total
                eta = timedelta(seconds=int(remaining / rate)) if rate > 0 else "?"
                log(f"  {model_name}: case {ci:,}/{len(cases):,}  "
                    f"| total {done_total:,}/{total_runs:,}  "
                    f"| {session_calls:,} new calls this session  "
                    f"| ETA {eta}")

    elapsed = timedelta(seconds=int(time.time() - start))
    log("\n" + "=" * 60)
    log(f"RUN COMPLETE (for available models)")
    log(f"  Completed case-model runs: {completed:,}")
    log(f"  Failures:                  {failed:,}")
    log(f"  New calls this session:    {session_calls:,}")
    log(f"  Elapsed:                   {elapsed}")
    log(f"  Cache totals per model:    {cache.stats()}")
    if skipped_models:
        log(f"  Still to do (download then re-run): {skipped_models}")
    log("=" * 60)


if __name__ == "__main__":
    main()
