"""
RareBench data loader and code-to-text converter.

Converts RareBench cases from their native format
    Phenotype:   ['HP:0001522', 'HP:0001942', ...]
    RareDisease: ['OMIM:251000', 'ORPHA:27', 'CCRD:71']
into clinical-vignette text using the HPO phenotype ontology and
the phenotype.hpoa disease-name mapping.
"""
import json
from pathlib import Path
from typing import Optional


def load_hpo_phenotype_lookup(hpo_json_path: Path) -> dict[str, str]:
    """Build a dict mapping HPO codes (HP:NNNNNNN) to their text labels."""
    with open(hpo_json_path) as f:
        hpo = json.load(f)

    lookup = {}
    for node in hpo["graphs"][0]["nodes"]:
        node_id = node.get("id", "")
        label = node.get("lbl", "")
        if "HP_" in node_id and label:
            code = node_id.split("/")[-1].replace("_", ":")
            lookup[code] = label
    return lookup


def load_disease_name_lookup(hpoa_path: Path) -> dict[str, str]:
    """Build a dict mapping disease codes (OMIM:..., ORPHA:...) to names."""
    lookup = {}
    with open(hpoa_path) as f:
        for line in f:
            if line.startswith("#") or line.startswith("database_id"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            code, name = parts[0].strip(), parts[1].strip()
            if code and name and code not in lookup:
                lookup[code] = name
    return lookup


def resolve_disease_name(
    disease_codes: list[str],
    disease_lookup: dict[str, str],
) -> Optional[str]:
    """
    Given a list of disease codes from a RareBench case, return the best
    human-readable name.

    Priority order: OMIM > ORPHA > DECIPHER > others.
    We prefer OMIM because it is the most widely cited in the literature,
    and falls back to ORPHA when OMIM is missing.
    """
    priority = ["OMIM", "ORPHA", "DECIPHER"]
    by_prefix = {code.split(":")[0]: code for code in disease_codes}

    for prefix in priority:
        if prefix in by_prefix:
            code = by_prefix[prefix]
            if code in disease_lookup:
                return disease_lookup[code]

    # Fall back to anything we can resolve
    for code in disease_codes:
        if code in disease_lookup:
            return disease_lookup[code]

    return None


def resolve_phenotype_labels(
    phenotype_codes: list[str],
    hp_lookup: dict[str, str],
) -> list[str]:
    """Map HPO codes to text labels, dropping any that can't be resolved."""
    labels = []
    for code in phenotype_codes:
        label = hp_lookup.get(code)
        if label:
            labels.append(label)
    return labels


def build_vignette(phenotype_labels: list[str]) -> str:
    """Construct a clinical-vignette prompt from a list of phenotype labels."""
    if not phenotype_labels:
        return ""
    features = ", ".join(phenotype_labels)
    return (
        "A patient presents with the following clinical features: "
        f"{features}. What is the most likely diagnosis?"
    )


def convert_case(
    raw_case: dict,
    hp_lookup: dict[str, str],
    disease_lookup: dict[str, str],
) -> Optional[dict]:
    """
    Convert one raw RareBench case to a standardized dict.

    Returns None if the case cannot be converted (no phenotypes resolve,
    or no disease name resolves).
    """
    phenotype_codes = raw_case.get("Phenotype") or []
    disease_codes = raw_case.get("RareDisease") or []

    phenotype_labels = resolve_phenotype_labels(phenotype_codes, hp_lookup)
    disease_name = resolve_disease_name(disease_codes, disease_lookup)

    if not phenotype_labels or not disease_name:
        return None

    return {
        "vignette": build_vignette(phenotype_labels),
        "ground_truth_dx": disease_name,
        "n_phenotypes": len(phenotype_labels),
        "raw_phenotype_codes": phenotype_codes,
        "raw_disease_codes": disease_codes,
    }
