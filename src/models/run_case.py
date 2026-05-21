"""
Run a single case through a single model with self-consistency.

For each (case, model):
  - 1 deterministic call  (temp 0.0, seed = BASE_SEED)         -> primary answer
  - N sampled calls       (temp 0.7, seeds = BASE_SEED+1..+N)  -> UQ signals

All calls are cached. Responses are parsed. Returns a CaseResult.
"""
from dataclasses import dataclass, field
from typing import Optional

from src.data.schema import Case, CaseFormat
from src.models.inference import call_model
from src.models.cache import ResponseCache
from src.models.parser import parse_response, ParsedResponse
from src.models.prompts import build_messages


BASE_SEED = 42
N_SAMPLES = 5
DETERMINISTIC_TEMP = 0.0
SAMPLING_TEMP = 0.7
MAX_TOKENS_DEFAULT = 1024  # uniform; Qwen2.5 is not a reasoning model


@dataclass
class SampleResult:
    sample_index: int
    temperature: float
    seed: int
    raw_text: str
    parsed: ParsedResponse
    provider: str
    finish_reason: Optional[str]
    from_cache: bool


@dataclass
class CaseResult:
    case_id: str
    model_name: str
    stratum: str
    is_multiple_choice: bool
    primary: SampleResult                       # the deterministic call
    samples: list[SampleResult] = field(default_factory=list)


def _max_tokens_for(model_name: str) -> int:
    return MAX_TOKENS_DEFAULT


def _one_call(
    model_name: str,
    case: Case,
    messages: list[dict],
    temperature: float,
    seed: int,
    sample_index: int,
    cache: ResponseCache,
) -> SampleResult:
    is_mc = case.format == CaseFormat.MULTIPLE_CHOICE
    cached = cache.get(model_name, messages, temperature, seed, sample_index)
    if cached is not None:
        parsed = parse_response(cached["text"], is_mc)
        return SampleResult(
            sample_index=sample_index,
            temperature=temperature,
            seed=seed,
            raw_text=cached["text"],
            parsed=parsed,
            provider=cached["provider"],
            finish_reason=cached["finish_reason"],
            from_cache=True,
        )

    resp = call_model(
        model_name,
        messages,
        temperature=temperature,
        max_tokens=_max_tokens_for(model_name),
        seed=seed,
    )
    cache.put(
        model_name=model_name,
        messages=messages,
        temperature=temperature,
        seed=seed,
        sample_index=sample_index,
        case_id=case.case_id,
        text=resp.text,
        finish_reason=resp.finish_reason,
        provider=resp.provider,
    )
    parsed = parse_response(resp.text, is_mc)
    return SampleResult(
        sample_index=sample_index,
        temperature=temperature,
        seed=seed,
        raw_text=resp.text,
        parsed=parsed,
        provider=resp.provider,
        finish_reason=resp.finish_reason,
        from_cache=False,
    )


def run_case(
    case: Case,
    model_name: str,
    cache: ResponseCache,
) -> CaseResult:
    messages = build_messages(case)
    is_mc = case.format == CaseFormat.MULTIPLE_CHOICE

    # Deterministic primary call (sample_index = -1 to distinguish it)
    primary = _one_call(
        model_name, case, messages,
        temperature=DETERMINISTIC_TEMP, seed=BASE_SEED,
        sample_index=-1, cache=cache,
    )

    # N sampled calls
    samples = []
    for i in range(N_SAMPLES):
        s = _one_call(
            model_name, case, messages,
            temperature=SAMPLING_TEMP, seed=BASE_SEED + 1 + i,
            sample_index=i, cache=cache,
        )
        samples.append(s)

    return CaseResult(
        case_id=case.case_id,
        model_name=model_name,
        stratum=case.stratum.value,
        is_multiple_choice=is_mc,
        primary=primary,
        samples=samples,
    )
