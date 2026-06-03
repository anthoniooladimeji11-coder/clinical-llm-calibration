"""
Answer grader for the calibration project.

Multiple-choice cases: exact letter match against ground truth.
Open-ended cases: LLM-as-judge using a neutral judge model.

Per D-024:
  - Default judge: gemma2-9b
  - To avoid self-judging, gemma2-9b is graded by llama-3.1-8b.
  - Judge calls are cached and deterministic (temperature 0, fixed seed).
"""
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from src.data.schema import Case, CaseFormat
from src.models.cache import ResponseCache
from src.models.inference import call_model

DEFAULT_JUDGE = "gemma2-9b"
SELF_JUDGE_FALLBACK = "llama-3.1-8b"
JUDGE_TEMPERATURE = 0.0
JUDGE_SEED = 42
JUDGE_MAX_TOKENS = 200


@dataclass
class GradeResult:
    correct: bool
    method: str
    judge_model: Optional[str] = None
    judge_verdict: Optional[str] = None
    judge_reason: Optional[str] = None
    judge_raw: Optional[str] = None
    notes: dict = None


_PROMPTS = None


def _load_judge_prompts(key: str = "judge") -> dict:
    """key is 'judge' (default) or 'judge_high_acuity'."""
    global _PROMPTS
    if _PROMPTS is None:
        with open(Path("configs/prompts.yaml")) as f:
            _PROMPTS = yaml.safe_load(f)
    return _PROMPTS[key]


def grade_multiple_choice(
    model_answer_letter: Optional[str],
    ground_truth_letter: str,
) -> GradeResult:
    if model_answer_letter is None:
        return GradeResult(
            correct=False, method="letter_match",
            notes={"reason": "model_answer_letter is None"},
        )
    correct = model_answer_letter.strip().upper() == ground_truth_letter.strip().upper()
    return GradeResult(correct=correct, method="letter_match")


_VERDICT_RE = re.compile(r"VERDICT:\s*(YES|NO)", re.IGNORECASE)
_REASON_RE = re.compile(r"REASON:\s*(.+?)(?:\n|$)", re.IGNORECASE | re.DOTALL)


def _parse_judge_output(text: str) -> tuple[str, Optional[str]]:
    m = _VERDICT_RE.search(text)
    if not m:
        return "UNPARSED", None
    verdict = m.group(1).upper()
    rm = _REASON_RE.search(text)
    reason = rm.group(1).strip() if rm else None
    return verdict, reason


def _pick_judge(model_under_test: str) -> str:
    if model_under_test == DEFAULT_JUDGE:
        return SELF_JUDGE_FALLBACK
    return DEFAULT_JUDGE


def _is_noise_answer(s: str) -> bool:
    """
    Detect parser-noise answers: single chars, markdown artefacts,
    answers too short to be a real diagnosis, or prose stubs starting
    with common reasoning openers (model failed to give a diagnosis).
    """
    if not s:
        return True
    stripped = s.strip().strip("*").strip("`").strip(":").strip()
    if len(stripped) < 4:
        return True
    # Pure punctuation / markdown
    if all(not c.isalnum() for c in stripped):
        return True
    # Common prose-stub starts that mean "model is reasoning, not naming a diagnosis"
    prose_starts = (
        "the patient", "the presence", "based on", "given the",
        "considering", "this patient", "in this case", "the clinical",
        "the most", "likely", "diagnosis:", "i think", "it is",
    )
    if stripped.lower().startswith(prose_starts):
        return True
    return False


def grade_open_ended(
    model_answer: Optional[str],
    ground_truth: str,
    model_under_test: str,
    cache: ResponseCache,
    high_acuity: bool = False,
) -> GradeResult:
    if not model_answer or not model_answer.strip():
        return GradeResult(
            correct=False, method="llm_judge",
            judge_verdict="NO",
            notes={"reason": "model_answer empty"},
        )

    if _is_noise_answer(model_answer):
        return GradeResult(
            correct=False, method="llm_judge",
            judge_verdict="NO",
            notes={"reason": "model_answer is parser-noise / non-diagnostic prose"},
        )

    prompt_key = "judge_high_acuity" if high_acuity else "judge"
    judge_prompts = _load_judge_prompts(prompt_key)
    judge_model = _pick_judge(model_under_test)
    user_prompt = judge_prompts["template"].format(
        answer=model_answer.strip(),
        ground_truth=ground_truth.strip(),
    )
    messages = [
        {"role": "system", "content": judge_prompts["system_prompt"].strip()},
        {"role": "user", "content": user_prompt},
    ]

    cached = cache.get(
        judge_model, messages,
        JUDGE_TEMPERATURE, JUDGE_SEED, -2,
    )
    if cached is not None:
        raw = cached["text"]
    else:
        resp = call_model(
            judge_model, messages,
            temperature=JUDGE_TEMPERATURE,
            max_tokens=JUDGE_MAX_TOKENS,
            seed=JUDGE_SEED,
        )
        raw = resp.text
        cache.put(
            model_name=judge_model,
            messages=messages,
            temperature=JUDGE_TEMPERATURE,
            seed=JUDGE_SEED,
            sample_index=-2,
            case_id=f"JUDGE::{model_under_test}",
            text=raw,
            finish_reason=resp.finish_reason,
            provider=resp.provider,
        )

    verdict, reason = _parse_judge_output(raw)
    correct = verdict == "YES"
    return GradeResult(
        correct=correct, method="llm_judge",
        judge_model=judge_model,
        judge_verdict=verdict,
        judge_reason=reason,
        judge_raw=raw,
    )


def grade_case_for_model(
    case: Case,
    primary_answer_letter: Optional[str],
    primary_answer_diagnosis: Optional[str],
    model_under_test: str,
    cache: ResponseCache,
) -> GradeResult:
    if case.format == CaseFormat.MULTIPLE_CHOICE:
        return grade_multiple_choice(
            primary_answer_letter, case.ground_truth_letter
        )
    else:
        from src.data.schema import Stratum
        is_high_acuity = case.stratum == Stratum.HIGH_ACUITY
        return grade_open_ended(
            primary_answer_diagnosis,
            case.ground_truth_text,
            model_under_test,
            cache,
            high_acuity=is_high_acuity,
        )
