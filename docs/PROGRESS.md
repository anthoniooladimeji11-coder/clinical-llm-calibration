# Project Progress

Tracking status against the 10-week plan. Updated as work completes.

Legend: ✅ done · 🟡 in progress · ⏳ not started · ❌ blocked

Last updated: 2026-05-18

---

## Phase 0 — Project scaffolding

| Item | Status |
|---|---|
| Repo created, venv, git, .gitignore | ✅ |
| GitHub remote connected | ✅ |
| Project installed in editable mode (pyproject.toml) | ✅ |
| README and structure | ✅ |
| WARP VPN active (workaround for HuggingFace throttling) | ✅ |

## Phase 1 — Methodology artifacts (Weeks 1–2)

| Item | Status | Notes |
|---|---|---|
| Stratum definitions (`configs/strata.yaml`) | ✅ | v0.1 draft; MedQA only for common stratum |
| Harm rubric (`configs/harm_rubric.yaml`) | ✅ | v0.1 draft; sent to Efosa for review |
| Harm rubric PDF for Efosa | ✅ | Sent |
| High-acuity keyword config (`configs/high_acuity_keywords.yaml`) | ✅ | v0.1 |
| Efosa rubric review | ⏳ | Awaiting response |

## Phase 2 — Data assembly (Weeks 2–3)

| Item | Status | Notes |
|---|---|---|
| MedQA download + explore | ✅ | 10,178 train + 1,273 test cases (GBaker 4-option mirror) |
| MedMCQA evaluated | ✅ | Rejected — mostly basic science not clinical |
| RareBench download + explore | ✅ | All 5 splits, 1,122 cases total |
| HPO ontology download | ✅ | 19,944 terms |
| Disease name mapping (phenotype.hpoa) | ✅ | 12,996 unique diseases |
| RareBench code-to-text converter | ✅ | `src/data/rarebench.py` |
| PMC-Patients download | ✅ | 180,142 entries via NCBI/Open-Patients mirror |
| High-acuity filter v0.1 | ✅ | Keyword only — too noisy (13,644 matches) |
| High-acuity filter v0.2 | ✅ | Tightened (head + admission context); 1,008 cases |
| Filtered PMC cases saved to disk | ✅ | `data/processed/pmc_high_acuity_v0.2.jsonl` |
| Unified case schema | ⏳ | Next |
| Stratified sampling | ⏳ | After unified schema |
| Final eval set (~2,000 cases) | ⏳ | End of Phase 2 |

## Phase 3 — Inference (Weeks 3–5)

| Item | Status |
|---|---|
| Groq API key set up | ⏳ |
| HuggingFace API key set up | ⏳ |
| Local model setup (MedGemma-4B via Ollama or llama.cpp) | ⏳ |
| Unified inference interface | ⏳ |
| Token logprobs extraction | ⏳ |
| Self-consistency sampling (5 samples × case × model) | ⏳ |
| Verbalized confidence prompting | ⏳ |
| Inference cache layer | ⏳ |
| Run all 4 models on full eval set | ⏳ |

## Phase 4 — UQ + Calibration (Weeks 5–6)

| Item | Status |
|---|---|
| Token entropy implementation | ⏳ |
| Semantic entropy implementation | ⏳ |
| Self-consistency variance implementation | ⏳ |
| Verbalized confidence parsing | ⏳ |
| Standard ECE per stratum | ⏳ |
| Harm-weighted ECE per stratum | ⏳ |
| Reliability diagrams (Figures 1–3) | ⏳ |
| Harm matrix rating with Efosa | ⏳ | After inference reveals actual dx pairs |

## Phase 5 — Abstention frontier (Weeks 6–7)

| Item | Status |
|---|---|
| Cost-ratio sweep (1:1 to 100:1) | ⏳ |
| Per-method abstention curves | ⏳ |
| Frontier visualization (Figures 4–5) | ⏳ |

## Phase 6 — Writing (Weeks 7–10)

| Item | Status |
|---|---|
| Methods + Results draft | ⏳ |
| Intro + Discussion | ⏳ |
| Efosa sanity-check read | ⏳ |
| Final revisions | ⏳ |
| Submission to npj Digital Medicine | ⏳ |
