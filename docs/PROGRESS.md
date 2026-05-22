# Project Progress

Last updated: 2026-05-21

## Phase overview

| Phase | Description | Status | Notes |
|------|-------------|--------|-------|
| 0 | Scaffolding | done | |
| 1 | Data assembly | done | Eval set v0.1 locked: 1,912 cases. |
| 2 | Inference (4 local models) | **running** | 2 of 4 models grinding; 2 pending download. |
| 3 | Answer grading | next | LLM-judge vs ontology-fuzzy decision pending. |
| 4 | Calibration analysis | not started | ECE + harm-weighted ECE per stratum. |
| 5 | Abstention frontier | not started | |
| 6 | Harm matrix rating | awaiting Efosa + graded pairs | Rubric v0.2 in review. |
| 7 | Writing | not started | Target: npj Digital Medicine. |

## Models (all local via Ollama)

| Model | Family | Params | Medical | Status |
|-------|--------|--------|---------|--------|
| llama-3.1-8b | Llama | 8B | no | downloaded, running |
| medgemma-4b | Gemma | 4B | yes | downloaded, running |
| qwen2.5-7b | Qwen | 7B | no | pending download |
| gemma2-9b | Gemma | 9B | no | pending download |

## Inference run

- Script: `scripts/20_run_inference.py` (resumable, crash-tolerant)
- Per case-model: 1 deterministic + 5 sampled calls (N=5, temp 0.7)
- Eval set: 1,912 cases -> ~11,500 calls per model
- Cache: `results/inference_cache.sqlite` (SQLite, idempotent)
- Estimated: several days on M1 Pro for all 4 models

## Harm rubric

- v0.1: drafted, sent to Efosa
- v0.2: standard-hospital + emergency/non-emergency axis (Efosa feedback)
- Status: draft, awaiting Efosa confirmation, then lock

## Outstanding

- Efosa confirmation of rubric v0.2
- Download qwen2.5-7b + gemma2-9b (blocked by network)
- Decide grading approach (LLM-judge vs ontology+fuzzy hybrid)
