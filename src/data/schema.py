"""
Unified case schema for the clinical LLM calibration project.

Every case from every source (MedQA, RareBench, PMC-Patients) gets
converted into a Case object. Downstream code (inference, UQ, grading)
reads only Cases and doesn't care about the original source format.
"""
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class Stratum(str, Enum):
    COMMON = "common"
    RARE = "rare"
    HIGH_ACUITY = "high_acuity"


class CaseFormat(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    OPEN_ENDED = "open_ended"


@dataclass
class Case:
    """A single evaluation case."""
    case_id: str
    source: str
    source_id: str
    stratum: Stratum
    format: CaseFormat
    vignette: str
    ground_truth_text: str
    ground_truth_letter: Optional[str] = None
    options: Optional[dict[str, str]] = None
    condition_tag: Optional[str] = None
    rare_disease_codes: Optional[list[str]] = None
    rare_phenotype_codes: Optional[list[str]] = None
    notes: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["stratum"] = self.stratum.value
        d["format"] = self.format.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Case":
        d = dict(d)
        d["stratum"] = Stratum(d["stratum"])
        d["format"] = CaseFormat(d["format"])
        return cls(**d)
