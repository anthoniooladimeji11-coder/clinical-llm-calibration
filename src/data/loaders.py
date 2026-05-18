"""
Loaders that convert each source dataset into a list of unified Case
objects.

Public functions:
  load_medqa_cases()        -> common stratum cases
  load_rarebench_cases()    -> rare stratum cases
  load_pmc_cases()          -> high-acuity stratum cases
  load_all_cases()          -> all three concatenated
"""
import json
from pathlib import Path

from datasets import load_dataset

from src.data.schema import Case, Stratum, CaseFormat
from src.data.rarebench import (
    load_hpo_phenotype_lookup,
    load_disease_name_lookup,
    convert_case as convert_rarebench_case,
)


def load_medqa_cases() -> list[Case]:
    """Load MedQA (USMLE 4-option) train split as Cases."""
    ds = load_dataset(
        "GBaker/MedQA-USMLE-4-options", split="train"
    )
    cases = []
    for i, ex in enumerate(ds):
        case = Case(
            case_id=f"medqa-train-{i:05d}",
            source="medqa",
            source_id=str(i),
            stratum=Stratum.COMMON,
            format=CaseFormat.MULTIPLE_CHOICE,
            vignette=ex["question"],
            ground_truth_text=ex["answer"],
            ground_truth_letter=ex["answer_idx"],
            options=ex["options"],
            notes={"meta_info": ex.get("meta_info")},
        )
        cases.append(case)
    return cases


def load_rarebench_cases() -> list[Case]:
    """Load all RareBench splits and convert codes to text vignettes."""
    hp_lookup = load_hpo_phenotype_lookup(
        Path("data/raw/hpo/hp.json")
    )
    disease_lookup = load_disease_name_lookup(
        Path("data/raw/hpo/phenotype.hpoa")
    )
    cases = []
    splits = ["RAMEDIS", "MME", "HMS", "LIRICAL"]
    for split_name in splits:
        ds = load_dataset(
            "chenxz/RareBench",
            split_name,
            split="test",
            trust_remote_code=True,
        )
        for i, ex in enumerate(ds):
            converted = convert_rarebench_case(
                ex, hp_lookup, disease_lookup
            )
            if converted is None:
                continue
            case_id = f"rarebench-{split_name.lower()}-{i:05d}"
            case = Case(
                case_id=case_id,
                source="rarebench",
                source_id=f"{split_name}-{i}",
                stratum=Stratum.RARE,
                format=CaseFormat.OPEN_ENDED,
                vignette=converted["vignette"],
                ground_truth_text=converted["ground_truth_dx"],
                rare_disease_codes=converted["raw_disease_codes"],
                rare_phenotype_codes=converted["raw_phenotype_codes"],
                notes={
                    "split": split_name,
                    "n_phenotypes": converted["n_phenotypes"],
                },
            )
            cases.append(case)
    return cases


def load_pmc_cases() -> list[Case]:
    """Load filtered PMC-Patients high-acuity cases from disk JSONL."""
    jsonl_path = Path("data/processed/pmc_high_acuity_v0.2.jsonl")
    if not jsonl_path.exists():
        raise FileNotFoundError(
            f"Expected filtered PMC file at {jsonl_path}. "
            "Run scripts/08_save_pmc_high_acuity.py first."
        )
    cases = []
    with open(jsonl_path) as f:
        for i, line in enumerate(f):
            row = json.loads(line)
            vignette = (
                row["description"]
                + "\n\nWhat is the most likely primary diagnosis?"
            )
            case = Case(
                case_id=f"pmc-{row['_id'].replace('pmc-', '')}",
                source="pmc",
                source_id=row["_id"],
                stratum=Stratum.HIGH_ACUITY,
                format=CaseFormat.OPEN_ENDED,
                vignette=vignette,
                ground_truth_text=row["condition"],
                condition_tag=row["condition"],
                notes={
                    "matched_term": row["matched_term"],
                    "filter_version": "v0.2",
                },
            )
            cases.append(case)
    return cases


def load_all_cases() -> list[Case]:
    """Load every case from every source."""
    return (
        load_medqa_cases()
        + load_rarebench_cases()
        + load_pmc_cases()
    )
