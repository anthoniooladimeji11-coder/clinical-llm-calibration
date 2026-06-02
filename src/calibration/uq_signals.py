"""
Compute uncertainty quantification signals from the cached self-consistency
samples for each (case, model).

Three signals (per D-022 — token entropy dropped because most local backends
don't expose logprobs):

  1. verbalized_confidence: the integer 0-100 the model wrote on the
     PRIMARY (deterministic) call. Already available on the grading row.
  2. self_consistency_variance: fraction of sampled answers that disagree
     with the modal (most common) answer across the N samples. 0.0 means
     all samples agreed; 1.0 - 1/N means maximum disagreement.
  3. semantic_entropy: Shannon entropy over the distribution of distinct
     answers across the N samples. Larger = the model wandered across
     more distinct options.

For multiple-choice cases we compare letters. For open-ended cases we
compare normalized lowercase strings (a coarse but reproducible match;
the LLM judge has already done the fine-grained equivalence for accuracy).
"""
import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Optional


@dataclass
class UQSignals:
    n_samples: int
    self_consistency_variance: Optional[float]   # 0..1, None if no samples
    semantic_entropy: Optional[float]            # >=0, None if no samples
    sample_answers_normalized: list[str]


_PUNCT_RE = re.compile(r"[^\w\s]")


def _normalize(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = s.strip().lower()
    s = _PUNCT_RE.sub("", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s or None


def compute_uq_from_samples(
    is_multiple_choice: bool,
    sample_answers: list[Optional[str]],
) -> UQSignals:
    """
    sample_answers: for MC, list of letters (A/B/C/D) or None;
                    for open-ended, list of diagnosis strings or None.
    """
    if is_multiple_choice:
        normalized = [
            (s.strip().upper() if s and s.strip() else None)
            for s in sample_answers
        ]
    else:
        normalized = [_normalize(s) for s in sample_answers]

    usable = [s for s in normalized if s]
    n = len(usable)
    if n == 0:
        return UQSignals(
            n_samples=0,
            self_consistency_variance=None,
            semantic_entropy=None,
            sample_answers_normalized=normalized,
        )

    counter = Counter(usable)
    modal_count = max(counter.values())
    variance = 1.0 - (modal_count / n)

    total = sum(counter.values())
    entropy = 0.0
    for c in counter.values():
        p = c / total
        if p > 0:
            entropy -= p * math.log(p)

    return UQSignals(
        n_samples=n,
        self_consistency_variance=variance,
        semantic_entropy=entropy,
        sample_answers_normalized=normalized,
    )
