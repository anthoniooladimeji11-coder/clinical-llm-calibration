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

## D-019: MedGemma 4B replaces BioMistral 7B as the medical model
**Date:** 2026-05-20
**Decision:** Use MedGemma 4B (Google, Gemma 3 base, instruction-tuned)
via Ollama as the medical-tuned model.
**Alternatives considered:** BioMistral 7B (chosen first), Meditron-7B,
MedGemma 27B, dropping the medical slot entirely.
**Reason:** BioMistral returned empty or prompt-echoing output under our
structured prompt — it is a base-style biomedical text model, not
instruction-tuned for QA format. Tuning a BioMistral-specific prompt
would break our shared-prompt fairness decision (D-018). MedGemma 4B is
instruction-tuned, follows the identical prompt cleanly (verified:
correct answer + ANSWER/CONFIDENCE format, no fallback), and fits the
M1 Pro 16GB constraint (27B too large).
**Risk:** MedGemma 4B is smaller (4B) than the other models. This is
itself interesting — it tests whether a small medical-tuned model
calibrates differently. Size difference noted in methods.
**Verified:** scripts/18_test_medgemma.py

---

## D-020: Self-consistency parameters (N=5, temp 0.7)
**Date:** 2026-05-20
**Decision:** Per (case, model): 1 deterministic call (temp 0.0) for the
primary graded answer, plus N=5 sampled calls (temp 0.7, distinct seeds)
for the UQ signals. Total 6 calls per (case, model).
**Alternatives considered:** N=3 (faster, ~2.5-day Qwen grind vs ~4-day).
**Reason:** The paper's core claim is about the behavior of uncertainty
signals. Self-consistency variance and semantic entropy both need enough
samples for a reliable estimate; N=5 gives more resolution than N=3.
Time is the only cost (run is unattended, resumable via cache), and we
are not on a hard deadline.
**Risk:** Longer inference run, especially for Qwen3 (token-heavy). Made
tractable by rate-limit backoff and the resumable cache.

## D-021: Rate-limit handling (Groq free tier)
**Date:** 2026-05-20
**Decision:** Groq calls retry up to 6 times with backoff. On a 429, we
parse the suggested wait from the error and sleep that long (plus
padding) before retrying. Ollama (local) needs no rate limiting.
**Reason:** Groq free tier caps tokens-per-minute (e.g. Qwen3 at 6,000
TPM). Qwen3's long <think> blocks (~3,000 tokens/call) exceed this in
two consecutive calls. Without backoff the full run would crash. With
it, the run self-throttles and completes unattended.
**Documented constraint:** Groq free-tier TPM limits make the full
inference run take several days, dominated by Qwen3. This is a practical
constraint of the zero-budget open-model setup, noted in methods.

---

## D-022: All-local small-model lineup (dropped Groq big models)
**Date:** 2026-05-21
**Decision:** Run four small open models entirely locally via Ollama:
Llama 3.1 8B, Qwen2.5 7B, Gemma2 9B, MedGemma 4B. Dropped Llama 3.3 70B
and Qwen3 32B (Groq).
**Alternatives considered:** Groq free tier (hit 100k tokens/day/model
hard limit — full run would take ~80 days/model); Groq Dev Tier (~$10-20,
but project has zero budget); trickle big models over weeks.
**Reason:** Groq free-tier daily token cap makes the full run infeasible
in reasonable calendar time, and there is no budget for paid tier. The
M1 Pro 16GB cannot run 32B-70B models. Four small models that fit in
16GB give architecture diversity (Llama, Qwen, Gemma families) at zero
cost with no rate limits — the full run becomes a single overnight job.
**Reframe:** Paper becomes "calibration failure in small open-weight
clinical LLMs deployable on consumer hardware" — more relevant to
low-resource health settings (aligns with the World Bank/GSBI context),
not less.
**Risk:** Cannot speak to large-model (>9B) behavior. Noted explicitly
in limitations as future work. Pilot suggests the overconfidence-on-
long-tail effect is, if anything, stronger in small models.
**Verified:** scripts/19_pilot_run.py — 42/42 parse success, both ready
models, all strata.

---

## D-023: Trimmed eval set (600 cases) and N=3 for local-compute tractability
**Date:** 2026-05-22
**Decision:** Run inference on a 600-case subset (200 common / 200 rare /
200 high-acuity, sampled with seed 42 from eval_set_v0.1) with N=3
self-consistency samples instead of N=5.
**Alternatives considered:** Full 1,912 cases at N=5 (the original plan);
N=2 + 300 cases (too weak for UQ); spreading the full run over many days.
**Reason:** Local inference on an M1 Pro 16GB runs ~1.5-2 min/case/model.
The full set at N=5 would take 1-2 weeks of dedicated machine time, which
is not feasible on the author's only computer. 600 cases keeps ~200 per
stratum (adequate for per-stratum ECE confidence intervals) and N=3 keeps
self-consistency / semantic-entropy estimates legitimate (N=3 is the
accepted floor; N=2 is not). Inference runs in resumable ~1-hour sessions
via the SQLite cache.
**Risk:** Smaller per-stratum N widens calibration confidence intervals;
N=3 gives coarser UQ resolution than N=5. Both noted in limitations.
High-acuity sub-conditions become small (will report per-condition n).
**Artifacts:** eval_set_v0.2_fast.jsonl + .meta.json; D-014/D-016 sizes
superseded for the inference run.

---

## D-024: Grading approach — LLM-as-judge with Gemma2 9B as neutral judge
**Date:** 2026-05-28
**Decision:** Multiple-choice (common stratum) graded by exact letter
match. Open-ended (rare + high-acuity) graded by Gemma2 9B acting as a
neutral judge, called at temperature 0 with a fixed prompt that asks
"do these two diagnoses refer to the same clinical condition: [answer]
vs [ground truth]?" The judge returns yes/no plus a one-line rationale.
**Alternatives considered:** Ontology + fuzzy hybrid (OMIM/Orphanet
synonym lookup + string similarity).
**Reason:** Models output diverse phrasings ("Hyper IgE syndrome",
"Job's syndrome", "Hyperimmunoglobulin E recurrent infection
syndrome" — same condition). Ontology lookup misses synonyms not in
HPO; fuzzy matching is brittle on long medical names. The high-acuity
stratum has coarse ground-truth tags (e.g. "sepsis") that don't map
cleanly to free-text answers via string methods. A semantic judge
handles both stratum formats uniformly.
**Mitigation of circularity:** Gemma2 9B grades the OTHER three models
(Llama 3.1 8B, Qwen2.5 7B, MedGemma 4B). For grading Gemma2 9B's own
answers, Llama 3.1 8B acts as the secondary judge. This avoids any
model judging itself.
**Reliability check:** A manual audit of ~150 judge decisions (50 per
stratum) will be done to estimate judge agreement with human grading.
**Determinism:** Judge temperature = 0, fixed seed, fixed prompt
template. All judge calls cached like inference calls.

---

## D-025: UQ signals — lexical-only self-consistency and semantic entropy
**Date:** 2026-06-03
**Decision:** Compute self-consistency variance and "semantic entropy"
using lexical (normalized-string) comparison of sampled answers, not
embedding- or judge-based semantic clustering.
**Alternatives considered:** Use an embedding model or an LLM-judge pass
to cluster semantically equivalent answers (e.g. "PKU" and "Phenylketonuria")
before computing entropy.
**Reason:** No embedding model is in the local pipeline, and adding an
LLM clustering pass would add ~900 more calls plus another layer of
judge dependence. Lexical comparison is the baseline used in early
self-consistency papers and is fully reproducible.
**Risk:** Overestimates uncertainty when a model uses synonyms (e.g.
"PKU" / "Phenylketonuria"). This biases UQ values upward on cases where
the model is actually consistent. Reported as a methods limitation;
future work can add embedding-based clustering.
**Implemented in:** `src/calibration/uq_signals.py`.

---

## D-026: Drop semantic entropy as a separate UQ method (degenerate at N=3)
**Date:** 2026-06-03
**Decision:** Report two UQ methods in the abstention frontier:
verbalized confidence and self-consistency variance. Drop semantic
entropy as a separately reported method.
**Reason:** With N=3 sampled answers (D-023), lexical semantic entropy
and self-consistency variance are near-degenerate — they ranked all
1,200 case-model rows identically to three decimal places. Reporting
both as distinct UQ methods would overstate the diversity of signals
compared.
**Risk:** Removes one of the four UQ methods originally proposed. The
remaining two are still genuinely different — verbalized is a self-report
made on a single deterministic call; variance measures behavioural
consistency across stochastic samples. A footnote in the paper notes
this and points to future work at higher N where entropy diverges
meaningfully.
**Stored in:** `scripts/28_figure_abstention_frontier.py`.

---

## D-027: Harm rubric locked at v1.0 (Efosa confirmation)
**Date confirmed by Iyawe:** 2026-05-25 (email: "this is confirmed")
**Date locked in repo:** 2026-06-03
**Decision:** Promote `configs/harm_rubric.yaml` from draft v0.2 to
locked v1.0. This is the rubric we and the co-rater (Dr. Efosa Iyawe)
will use for the harm-matrix rating.
**Provenance trail:**
  1. v0.1 drafted and emailed to Iyawe on 2026-05-18 (PDF attachment).
  2. Iyawe feedback on 2026-05-22: change "well-resourced hospital" to
     "standard hospital"; reorganize scale around an emergency vs.
     non-emergency axis between levels 3 and 4; move pulmonary
     embolism from 3 to 4.
  3. v0.2 revised on 2026-05-21 and re-sent inline for confirmation.
  4. Iyawe confirmed on 2026-05-25.
**Note on the gap:** Rubric was kept at status `draft` in the repo
from 2026-05-25 to 2026-06-03 because subsequent work focused on
inference and calibration analysis. No rating decisions were taken
during that period, so the gap does not affect any results.
**Next step:** Phase 6 — generate the rating spreadsheet from the
graded (true_dx, predicted_dx) pairs and send to Iyawe.

---
