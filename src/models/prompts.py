"""
Build prompts from configs/prompts.yaml for a given Case.
"""
from pathlib import Path

import yaml

from src.data.schema import Case, CaseFormat

_PROMPTS = None


def _load_prompts() -> dict:
    global _PROMPTS
    if _PROMPTS is None:
        with open(Path("configs/prompts.yaml")) as f:
            _PROMPTS = yaml.safe_load(f)
    return _PROMPTS


def build_messages(case: Case) -> list[dict]:
    """Build the chat messages (system + user) for a case."""
    cfg = _load_prompts()
    system = cfg["system_prompt"].strip()

    if case.format == CaseFormat.MULTIPLE_CHOICE:
        opts = case.options or {}
        user = cfg["multiple_choice"]["template"].format(
            vignette=case.vignette.strip(),
            option_a=opts.get("A", ""),
            option_b=opts.get("B", ""),
            option_c=opts.get("C", ""),
            option_d=opts.get("D", ""),
        )
    else:
        user = cfg["open_ended"]["template"].format(
            vignette=case.vignette.strip(),
        )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
