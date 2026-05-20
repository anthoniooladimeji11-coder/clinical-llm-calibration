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

## D-010: Native format per stratum (not forced multiple choice)
**Date:** 2026-05-18
**Decision:** MedQA stays multiple choice; RareBench and PMC stay
open-ended. Don't generate distractors for the open-ended cases.
**Alternatives considered:** Force everything to MC; force everything
to open-ended.
**Reason:** Generating defensible distractors for rare and high-acuity
cases is its own methodological problem. Native format respects each
dataset and is what recent papers in the field do.
**Risk:** Grading is format-specific. We handle this with LLM-as-judge
for open-ended.

---

## D-011: Ground truth representation per stratum
**Date:** 2026-05-18
**Decision:** Common = option letter + text; Rare = full disease name +
phenotype/disease codes preserved; High-acuity = coarse condition tag
(acute_mi, sepsis, etc.) plus the matched keyword.
**Alternatives considered:** Extract specific diagnoses from PMC case
text; use only the option letter for MedQA.
**Reason:** Each stratum's natural ground truth is what we record.
PMC coarse tags map cleanly to ICD-10 anchors for the harm matrix.
**Risk:** PMC grading is coarse — model gets credit for naming any
acute MI variant rather than the specific one in the case. Acceptable.

---

## D-012: LLM-as-judge for open-ended grading
**Date:** 2026-05-18
**Decision:** Use Llama 3.3 70B via Groq (free tier) to grade open-ended
answers against ground truth. Audit 200 cases manually for IRR with
the LLM judge.
**Alternatives considered:** Strict string match; full manual grading;
embedding similarity.
**Reason:** Standard in 2024-2025 medical-LLM evaluation papers. Free
under Groq free tier. Manual audit provides reviewer confidence.
**Risk:** Judge model may be biased toward over-generous grading.
Audit will quantify this.

---

## D-013: Pediatric exclusion for common stratum
**Date:** 2026-05-18
**Decision:** Regex-based filter drops MedQA cases that open with
pediatric subjects (e.g. "A 3-month-old", "A newborn", "A 12-year-old").
**Alternatives considered:** Keep pediatric cases, handle at harm-rating
time.
**Reason:** Harm rubric assumes adults. Filtering at sampling is
cleaner than carrying a pediatric flag through every downstream step.
1,693 / 10,178 cases dropped (~17%).
**Risk:** Some edge-case wording may slip through. Spot checks looked
clean.

---

## D-014: Balanced within-stratum sampling for high-acuity
**Date:** 2026-05-18
**Decision:** Cap each high-acuity condition at 70 cases. Take all
available cases when fewer than 70 exist (ischemic_stroke n=20,
acute_pulmonary_oedema n=29, diabetic_emergency n=43).
**Alternatives considered:** Random sample 600 from the full pool
(would have been ~210 sepsis cases).
**Reason:** The whole paper is about stratum-specific failures. Each
sub-condition needs representation to detect calibration gaps.
**Risk:** Ischemic stroke n=20 gives wide CIs. Acknowledged in
limitations.

---

## D-015: Rare quality filter — min 3 phenotypes + label-leakage check
**Date:** 2026-05-18
**Decision:** Drop rare cases with <3 phenotypes OR with any phenotype
label >=70% similar to the ground-truth disease name.
**Alternatives considered:** No filter; length-only filter; manual review.
**Reason:** Cases with very few phenotypes or with diagnostic-finding
labels are trivially easy. The filter dropped 111 / 1,121 cases (~10%).
**Risk:** Some leaky pairs slip through (e.g. "Hyperphenylalaninemia"
phenotype with "Phenylketonuria" diagnosis — same condition, low string
similarity). Mentioned in discussion.

---

## D-016: Unequal final Ns across strata
**Date:** 2026-05-18
**Decision:** Accept 800/600/512 final stratum sizes. Do not downsample
common/rare to match high-acuity.
**Alternatives considered:** Equal Ns at 512.
**Reason:** Throwing away 776 cases for balance hurts statistical power
where we have it. Calibration metrics work fine with unequal Ns.
**Risk:** Cross-stratum comparisons need to weight by stratum size or
report separately. We do the latter.

---

## D-017: Qwen3 32B replaces Mixtral 8x7B
**Date:** 2026-05-19
**Decision:** Use Qwen3 32B (via Groq) as the fourth-architecture model
instead of Mixtral 8x7B.
**Alternatives considered:** gpt-oss-20b/120b (different lineage but
naming risks confusion with GPT-4), Llama 4 Scout (still Llama family),
allam-2-7b (Arabic-focused).
**Reason:** Groq decommissioned `mixtral-8x7b-32768` (confirmed via API
error). Qwen3 32B is a genuinely different model family (not Llama, not
Mistral), well-benchmarked, and widely used in 2025-2026 research, so it
preserves the cross-architecture generalizability check Mixtral provided.
**Risk:** Qwen3 is a reasoning model that emits <think>...</think> blocks.
The response parser must strip these before extracting answer +
confidence. Noted for the inference parser.

---

## D-018: Prompt design — CoT, verbalized 0-100 confidence, shared prompt
**Date:** 2026-05-19
**Decision:** One multiple-choice template (common stratum) and one
open-ended template (rare + high-acuity). Chain-of-thought reasoning
allowed. Verbalized confidence elicited as integer 0-100. Identical
prompt across all four models. Tolerant parser with fallbacks; parse-
failure rate reported per model.
**Alternatives considered:** Bare answer (no CoT); word-scale confidence
(low/med/high); per-model tuned prompts.
**Reason:** CoT reflects real deployment and makes the "confidently
wrong after reasoning" finding visible. 0-100 integer maps cleanly to a
probability for calibration. Shared prompt keeps the cross-model
comparison fair. Parse-failure rate is itself a reportable signal.
**Risk:** BioMistral (small, weakly instruction-tuned) and Qwen3
(emits <think> tags) may not follow the format reliably. Mitigated by a
tolerant parser and a 20-case pilot before the full run.
**Stored in:** `configs/prompts.yaml`

---
