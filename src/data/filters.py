"""
Stratum-specific quality and exclusion filters.

These run during eval-set construction, after the unified loaders but
before stratified sampling.
"""
import re
from difflib import SequenceMatcher

from src.data.schema import Case


# ----- Pediatric exclusion for the common stratum -----

# Patterns that indicate a pediatric case based on the opening of a
# clinical vignette. Conservative: only triggers on clear age indicators
# at the start, not on incidental mentions ("the patient's child...").
_PEDIATRIC_PATTERNS = [
    # Age in months/days/weeks/hours at vignette start
    r"^\s*A\s+\d+[-\s]?(?:month|day|week|hour)[s\-]?[-\s]?old",
    # "A newborn", "A neonate", "A premature infant"
    r"^\s*A\s+(?:newborn|neonate|premature infant|preterm infant|infant)",
    # Explicit pediatric ages (1-17) at vignette start
    r"^\s*A\s+(?:1[0-7]|[1-9])[-\s]?year[s\-]?[-\s]?old",
    # "A child", "A boy", "A girl" without qualifying adult age
    r"^\s*A\s+(?:child|boy|girl|toddler|infant)\b",
    # "An X-month-old"
    r"^\s*An?\s+\d+[-\s]?(?:month|day|week|hour)[s\-]?[-\s]?old",
]

_PED_REGEXES = [re.compile(p, re.IGNORECASE) for p in _PEDIATRIC_PATTERNS]


def is_pediatric_vignette(text: str) -> bool:
    """Return True if the vignette opens with a clearly pediatric subject."""
    if not text:
        return False
    head = text[:120]  # only check the opening of the vignette
    return any(rx.search(head) for rx in _PED_REGEXES)


def exclude_pediatric(cases: list[Case]) -> list[Case]:
    """Drop cases whose vignette begins with a pediatric subject."""
    return [c for c in cases if not is_pediatric_vignette(c.vignette)]


# ----- Quality filter for the rare stratum -----

LABEL_LEAKAGE_SIMILARITY = 0.70   # if any phenotype is >=70% similar to dx
MIN_PHENOTYPES = 3                # require at least 3 phenotypes


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def has_label_leakage(case: Case) -> bool:
    """
    True if any phenotype label is suspiciously similar to the ground-
    truth disease name (e.g. an enzyme-activity finding that names the
    disease). These cases are too easy for the model.
    """
    dx = case.ground_truth_text or ""
    if not dx:
        return False
    # Extract phenotype labels from the vignette. The converter formats
    # phenotypes after the colon, separated by commas, ending in a period
    # before the question.
    m = re.search(
        r"clinical features:\s*(.*?)\.\s*What is the most likely",
        case.vignette,
    )
    if not m:
        return False
    phenotype_text = m.group(1)
    phenotypes = [p.strip() for p in phenotype_text.split(",")]
    for p in phenotypes:
        if _similarity(p, dx) >= LABEL_LEAKAGE_SIMILARITY:
            return True
    return False


def apply_rare_quality_filter(cases: list[Case]) -> list[Case]:
    """Drop rare cases that are too easy (label leakage or <3 phenotypes)."""
    out = []
    for c in cases:
        n_phen = c.notes.get("n_phenotypes", 0)
        if n_phen < MIN_PHENOTYPES:
            continue
        if has_label_leakage(c):
            continue
        out.append(c)
    return out
