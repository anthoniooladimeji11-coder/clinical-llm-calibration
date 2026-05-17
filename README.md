# Clinical LLM Calibration

**Working title:** Long-Tail Calibration Failure in Clinical LLMs:
Harm-Weighted Uncertainty Evaluation Reveals Hidden Overconfidence on
Rare and High-Acuity Presentations.

## One-line summary
LLMs in medical reasoning appear well-calibrated on average but become
catastrophically overconfident on rare diseases, atypical presentations,
and high-acuity cases. This project measures that gap with harm-weighted
calibration metrics and a cost-asymmetric abstention frontier.

## Contributions
1. Stratified calibration analysis across common, rare, and high-acuity strata.
2. Head-to-head comparison of four uncertainty signals under harm-weighted ECE.
3. Abstention frontier under varying false-negative / false-positive cost ratios.

## Status
Week 0 — project scaffolding.

## Structure
- `configs/`   — frozen experiment configs (strata, harm matrix, models)
- `data/`      — raw, processed, and harm-matrix ratings (gitignored)
- `src/`       — library code
- `scripts/`   — entry points run from the terminal
- `results/`   — model outputs and metrics (gitignored)
- `figures/`   — paper figures
- `tests/`     — unit tests

## Setup
\`\`\`
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
\`\`\`
