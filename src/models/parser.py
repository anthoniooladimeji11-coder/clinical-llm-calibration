"""
Parse raw model output into a structured ParsedResponse.

Handles:
  - Stripping Qwen3 <think>...</think> reasoning blocks.
  - Strict format: 'ANSWER: X' / 'DIAGNOSIS: ...' + 'CONFIDENCE: NN'.
  - Looser fallbacks when the model doesn't follow the format exactly.
  - Flagging parse failures (answer or confidence not found).
"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedResponse:
    answer_letter: Optional[str] = None      # A/B/C/D for multiple choice
    diagnosis: Optional[str] = None          # free text for open-ended
    confidence: Optional[int] = None         # 0-100
    answer_parse_ok: bool = False
    confidence_parse_ok: bool = False
    used_fallback: bool = False
    cleaned_text: str = ""                   # text after stripping think tags


_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_OPEN_THINK_RE = re.compile(r"<think>.*$", re.DOTALL | re.IGNORECASE)


def strip_think_tags(text: str) -> str:
    """Remove <think>...</think> blocks (and any unclosed trailing one)."""
    text = _THINK_RE.sub("", text)
    text = _OPEN_THINK_RE.sub("", text)  # handle truncated/unclosed think
    return text.strip()


# ---- Confidence ----

_CONF_STRICT = re.compile(r"CONFIDENCE:\s*(\d{1,3})", re.IGNORECASE)
_CONF_LOOSE = [
    re.compile(r"confidence[^\d]{0,15}(\d{1,3})\s*%?", re.IGNORECASE),
    re.compile(r"(\d{1,3})\s*%\s*confiden", re.IGNORECASE),
    re.compile(r"probability[^\d]{0,15}(\d{1,3})\s*%?", re.IGNORECASE),
]


def _extract_confidence(text: str) -> tuple[Optional[int], bool, bool]:
    """Return (confidence, ok, used_fallback)."""
    m = _CONF_STRICT.search(text)
    if m:
        val = int(m.group(1))
        if 0 <= val <= 100:
            return val, True, False
    for rx in _CONF_LOOSE:
        m = rx.search(text)
        if m:
            val = int(m.group(1))
            if 0 <= val <= 100:
                return val, True, True
    return None, False, False


# ---- Multiple-choice answer ----

_ANS_STRICT = re.compile(r"ANSWER:\s*([A-D])", re.IGNORECASE)
_ANS_LOOSE = [
    re.compile(r"\bthe answer is\s*\(?([A-D])\)?", re.IGNORECASE),
    re.compile(r"\boption\s*\(?([A-D])\)?", re.IGNORECASE),
    re.compile(r"\banswer\b[^A-D]{0,10}\b([A-D])\b", re.IGNORECASE),
    re.compile(r"^\s*\(?([A-D])\)?\s*$", re.IGNORECASE | re.MULTILINE),
]


def _extract_letter(text: str) -> tuple[Optional[str], bool, bool]:
    m = _ANS_STRICT.search(text)
    if m:
        return m.group(1).upper(), True, False
    for rx in _ANS_LOOSE:
        m = rx.search(text)
        if m:
            return m.group(1).upper(), True, True
    return None, False, False


# ---- Open-ended diagnosis ----

_DX_STRICT = re.compile(r"DIAGNOSIS:\s*(.+?)(?:\n|$)", re.IGNORECASE)
_DX_LOOSE = [
    re.compile(r"most likely diagnosis is[:\s]*(.+?)(?:\.|\n|$)", re.IGNORECASE),
    re.compile(r"diagnosis[:\s]+(.+?)(?:\.|\n|$)", re.IGNORECASE),
]


def _extract_diagnosis(text: str) -> tuple[Optional[str], bool, bool]:
    m = _DX_STRICT.search(text)
    if m:
        dx = m.group(1).strip().strip(".")
        if dx:
            return dx, True, False
    for rx in _DX_LOOSE:
        m = rx.search(text)
        if m:
            dx = m.group(1).strip().strip(".")
            if dx:
                return dx, True, True
    return None, False, False


# ---- Public ----

def parse_response(raw_text: str, is_multiple_choice: bool) -> ParsedResponse:
    cleaned = strip_think_tags(raw_text)

    conf, conf_ok, conf_fb = _extract_confidence(cleaned)

    if is_multiple_choice:
        letter, ans_ok, ans_fb = _extract_letter(cleaned)
        return ParsedResponse(
            answer_letter=letter,
            confidence=conf,
            answer_parse_ok=ans_ok,
            confidence_parse_ok=conf_ok,
            used_fallback=(ans_fb or conf_fb),
            cleaned_text=cleaned,
        )
    else:
        dx, ans_ok, ans_fb = _extract_diagnosis(cleaned)
        return ParsedResponse(
            diagnosis=dx,
            confidence=conf,
            answer_parse_ok=ans_ok,
            confidence_parse_ok=conf_ok,
            used_fallback=(ans_fb or conf_fb),
            cleaned_text=cleaned,
        )
