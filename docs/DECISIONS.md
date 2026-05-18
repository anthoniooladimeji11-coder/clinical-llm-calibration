# Methodology Decisions Log

Every non-trivial methodology choice, with the alternatives considered and
the reasoning. This is the document we hand a reviewer who asks "why did
you do it this way?"

Last updated: 2026-05-18

---

## D-001 — Drop GPT-4o and Claude from model lineup
- **Date:** 2026-05-17
- **Choice:** Use only open-source models accessible via Groq free tier + local inference.
- **Alternatives considered:** API access to GPT-4o + Claude (~$150 cost).
- **Reasoning:** Zero-budget constraint. Reframes the paper around open-source clinical LLMs — actually a stronger angle for the venue (reproducibility, deployability in real hospitals).

## D-002 — Stratum: Common / Rare / High-acuity
- **Date:** 2026-05-17
- **Choice:** Three strata with target N ~800/600/600.
- **Reasoning:** Need enough cases per stratum for statistical power on ECE confidence intervals (~400-600 min). Three strata cover the central hypothesis without bloating the project.

## D-003 — Harm framing: B (population-average) with C and D as anchors
- **Date:** 2026-05-17
- **Choice:** Score average expected harm to a patient population if the AI's prediction is followed. Use treatment divergence (C) and mortality/morbidity gap (D) as anchoring questions when ambiguous.
- **Alternatives considered:** A (specific patient), C alone (treatment divergence), D alone (mortality risk).
- **Reasoning:** B is stable across contexts. C and D provide concrete reference points for resolving disagreement between raters. Better inter-rater reliability than A.

## D-004 — Harm rubric assumptions
- **Date:** 2026-05-17
- **Choices:**
  - Healthcare setting: well-resourced general hospital.
  - Patient population: adult patients only (pediatric excluded).
  - Harm dimensions: clinical harm broadly, including major psychological/family sequelae. Not separately scored.
- **Reasoning:** Maximize reproducibility and inter-rater agreement. Acknowledged as limitations in discussion.

## D-005 — Drop MedMCQA, use MedQA only for common stratum
- **Date:** 2026-05-17
- **Alternatives considered:** Keep MedMCQA and filter by `subject_name` for clinical subjects only.
- **Reasoning:** MedMCQA is mostly basic science (physiology, anatomy, etc.), not clinical vignettes. Mixing it with MedQA creates a heterogeneous common stratum. MedQA's 10,178 clinical vignettes is more than enough for our 800-case target.

## D-006 — MedQA: use 4-option mirror (GBaker), not 5-option original (bigbio)
- **Date:** 2026-05-17
- **Reasoning:** Recent LLM-medical calibration papers standardized on the 4-option version. Comparability with prior work. Cleaner format. Smaller download (10 MB vs 132 MB).

## D-007 — RareBench: Path B (convert codes to natural-language vignettes)
- **Date:** 2026-05-17
- **Alternatives considered:** Path A (use HPO codes directly as model input).
- **Reasoning:** Path B is what the RareBench paper authors themselves do when prompting GPT-4. Makes rare cases comparable in format to MedQA and PMC-Patients (all narrative text). Avoids a heterogeneous schema.

## D-008 — PMC-Patients: NCBI/Open-Patients mirror
- **Date:** 2026-05-17
- **Alternatives considered:** zhengyun21/PMC-Patients (V2, ~837 MB JSON); direct Figshare download.
- **Reasoning:** NCBI mirror is smaller (~482 MB), cleaner format (`_id` + `description`), and includes USMLE notes we can filter out. Published by NCBI itself, defensible provenance.

## D-009 — High-acuity filter: keyword-based, not ICD-based
- **Date:** 2026-05-18
- **Choice:** Filter PMC-Patients by clinical keyword matching, with positional + admission-context constraints.
- **Alternatives considered:** ICD-10 code filtering (PMC-Patients has no ICD codes), UMLS-mapped vocabulary filtering (too heavy for the project scope), LLM-based second pass (adds dependency).
- **Reasoning:** PMC-Patients has no ICD codes attached. Keyword filtering is transparent, reproducible, and tunable. We accept ~10-15% false-positive rate as a known limitation.

## D-010 — High-acuity filter v0.2 over v0.1
- **Date:** 2026-05-18
- **Choice:** Require keyword to appear in first 500 characters AND within 60 characters of an admission/presentation phrase.
- **Reasoning:** v0.1 had ~50% false-positive rate from incidental mentions in long case narratives. v0.2 drops total matches from 13,644 to 1,008 but raises true-positive rate to ~85-90% in spot checks. 1,008 is still well above the 600-case target.

## D-011 — Pediatric exclusion at sampling stage, not filter stage
- **Date:** 2026-05-18
- **Reasoning:** Some pediatric cases survive the high-acuity filter. Harm rubric is adult-only. Cleanest place to enforce age constraint is during stratified sampling, where we already filter for case quality.
