"""
PMC-Patients loader and high-acuity filter.

Loads cases from the ncbi/Open-Patients mirror, filters out non-PMC
entries (USMLE cases), then applies keyword-based high-acuity filtering
defined in configs/high_acuity_keywords.yaml.

Two filter modes are provided:

  - find_first_matching_condition (loose):
        matches any occurrence of a keyword anywhere in the text,
        excluding history-context mentions.

  - find_first_matching_condition_tight (strict):
        requires the keyword to appear in the first N characters of
        the text AND within an admission-context window. Far fewer
        false positives, used for the high-acuity stratum.
"""
import re
from pathlib import Path
from typing import Iterable, Optional

import yaml


def load_keyword_config(config_path: Path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def _build_patterns(config: dict) -> dict[str, re.Pattern]:
    """One combined regex per condition (alternation), case-insensitive."""
    patterns = {}
    for condition_name, condition_data in config["conditions"].items():
        sorted_kws = sorted(
            condition_data["keywords"], key=len, reverse=True
        )
        escaped = [re.escape(kw) for kw in sorted_kws]
        joined = "|".join(escaped)
        pattern = re.compile(
            rf"(?:^|(?<=[\s,.;:()\[\]]))"
            rf"(?:{joined})"
            rf"(?:$|(?=[\s,.;:()\[\]]))",
            flags=re.IGNORECASE,
        )
        patterns[condition_name] = pattern
    return patterns


_HISTORY_REGEX = re.compile(
    r"\b(history of|h/o|previous|prior|past medical history of|"
    r"remote history)\s*\w*\s*$",
    flags=re.IGNORECASE,
)


_ADMISSION_CONTEXT_REGEX = re.compile(
    r"\b("
    r"presented with|presenting with|presents with|presented in|"
    r"admitted with|admitted for|admitted to|admission for|"
    r"diagnosed with|diagnosis of|"
    r"was found to have|found to have|"
    r"developed|developing|"
    r"was treated for|treated for|"
    r"complaining of|complained of|"
    r"referred for|referred with|"
    r"transferred for|transferred with|"
    r"brought in with|brought to.*with"
    r")\b",
    flags=re.IGNORECASE,
)


def _is_history_mention(text: str, match_start: int) -> bool:
    window_start = max(0, match_start - 50)
    preceding = text[window_start:match_start]
    return bool(_HISTORY_REGEX.search(preceding))


def _has_admission_context(text: str, match_start: int, match_end: int) -> bool:
    """
    Check if there's an admission-context phrase within 80 chars before
    OR 30 chars after the keyword match.
    """
    before_start = max(0, match_start - 80)
    after_end = min(len(text), match_end + 30)
    window = text[before_start:after_end]
    return bool(_ADMISSION_CONTEXT_REGEX.search(window))


def find_first_matching_condition(
    text: str,
    patterns: dict[str, re.Pattern],
) -> Optional[tuple[str, str]]:
    """Loose filter: any keyword match, excluding history mentions."""
    if not text:
        return None
    for condition_name, pattern in patterns.items():
        for m in pattern.finditer(text):
            if _is_history_mention(text, m.start()):
                continue
            return condition_name, m.group(0)
    return None


def find_first_matching_condition_tight(
    text: str,
    patterns: dict[str, re.Pattern],
    position_cutoff: int = 500,
) -> Optional[tuple[str, str]]:
    """
    Tight filter for high-acuity stratum:
      1. Keyword must appear in the first `position_cutoff` characters.
      2. Keyword must not be in a history-mention context.
      3. Keyword must be near an admission-context phrase.
    """
    if not text:
        return None
    head = text[:position_cutoff]
    for condition_name, pattern in patterns.items():
        for m in pattern.finditer(head):
            if _is_history_mention(head, m.start()):
                continue
            if not _has_admission_context(head, m.start(), m.end()):
                continue
            return condition_name, m.group(0)
    return None


def filter_pmc_for_high_acuity(
    dataset: Iterable[dict],
    config: dict,
    tight: bool = True,
    verbose: bool = True,
) -> list[dict]:
    """
    Iterate a dataset, keep only PMC entries whose description matches
    at least one high-acuity keyword.

    If tight=True (default), uses the strict admission-context filter.
    """
    patterns = _build_patterns(config)
    finder = (
        find_first_matching_condition_tight if tight
        else find_first_matching_condition
    )
    out = []
    for i, ex in enumerate(dataset):
        if verbose and i and i % 20000 == 0:
            print(f"  ...scanned {i:,} entries, matched {len(out):,} so far")
        case_id = str(ex.get("_id", ""))
        if not case_id.startswith("pmc-"):
            continue
        text = ex.get("description", "") or ""
        match = finder(text, patterns)
        if match is None:
            continue
        condition_name, matched_term = match
        out.append({
            "_id": case_id,
            "description": text,
            "condition": condition_name,
            "matched_term": matched_term,
        })
    return out
