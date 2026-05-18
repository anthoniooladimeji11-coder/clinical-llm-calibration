# Project Progress

Last updated: 2026-05-18

## Phase overview

| Phase | Description | Status | Notes |
|------|-------------|--------|-------|
| 0 | Scaffolding (repo, venv, git, configs) | done | All scaffolding committed. |
| 1 | Data assembly | **done** | Eval set v0.1 locked: 1,912 cases. |
| 2 | Inference (4 models x 1,912 cases) | next | Groq API setup pending. |
| 3 | UQ computation | not started | Token entropy, semantic entropy, self-consistency, verbalized. |
| 4 | Calibration analysis | not started | ECE + harm-weighted ECE per stratum. |
| 5 | Abstention frontier | not started | Cost-asymmetric curves. |
| 6 | Harm matrix rating | awaiting Efosa | Rubric v0.1 sent; rating happens in weeks 5-6 from inference outputs. |
| 7 | Writing | not started | Target venue: npj Digital Medicine. |

## Phase 1 (data assembly) — complete

| Step | Status | Output |
|------|--------|--------|
| Stratum definitions config | locked v0.1 | `configs/strata.yaml` |
| Harm rubric config | draft v0.1 (sent to Efosa) | `configs/harm_rubric.yaml` |
| MedQA exploration | done | 10,178 train cases via `GBaker/MedQA-USMLE-4-options` |
| MedMCQA exploration | rejected | Mostly basic-science, not clinical vignettes |
| RareBench: HPO ontology + converter | done | `src/data/rarebench.py`, 1,121 convertible cases |
| PMC-Patients: keyword filter v0.2 | locked | `src/data/pmc_patients.py`, 1,008 filtered cases |
| Unified Case schema | locked | `src/data/schema.py` |
| Per-source loaders | done | `src/data/loaders.py` |
| Stratum-specific filters | done | `src/data/filters.py` (pediatric, rare quality) |
| Locked evaluation set v0.1 | done | `data/processed/eval_set_v0.1.jsonl` |

## Evaluation set v0.1 — final composition

| Stratum | Source | n | Notes |
|---------|--------|---|-------|
| Common | MedQA (post-pediatric filter) | 800 | sampled from 8,485 |
| Rare | RareBench (post-quality filter) | 600 | sampled from 1,010 |
| High-acuity | PMC-Patients (balanced by condition) | 512 | capped 70 per condition |
| **Total** | | **1,912** | |

High-acuity per-condition breakdown:

| Condition | n |
|-----------|---|
| sepsis | 70 |
| acute_mi | 70 |
| acute_pancreatitis | 70 |
| hemorrhagic_stroke | 70 |
| shock | 70 |
| pulmonary_embolism | 70 |
| diabetic_emergency | 43 |
| acute_pulmonary_oedema | 29 |
| ischemic_stroke | 20 |

## Figures so far

- Figure 1 (draft v0.2): dataset flow diagram — `figures/dataset_flow_v0.2.png`

## External dependencies / outstanding

- Efosa's review of harm rubric v0.1 (sent 2026-05-17; expected within ~1 week)
- Groq API key needed before inference phase
- Cloudflare WARP currently on (HuggingFace access via Nigerian ISP needed it)
