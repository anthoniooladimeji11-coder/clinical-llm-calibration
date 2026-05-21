"""
Unified model-calling interface.

call_model(model_name, messages, ...) routes to Groq or Ollama based on
configs/models.yaml, and returns a standardized ModelResponse regardless
of backend. Groq calls retry with backoff on rate-limit (429) errors.

This module does ONE thing: call a model and return raw output.
Prompt construction, parsing, caching, and self-consistency live elsewhere.
"""
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import requests
import yaml
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = "http://localhost:11434"

# Rate-limit retry settings (Groq)
MAX_RETRIES = 6
DEFAULT_BACKOFF_SECONDS = 20.0
BACKOFF_PADDING = 1.5  # add a little extra to the suggested wait


@dataclass
class TokenLogprob:
    token: str
    logprob: float


@dataclass
class ModelResponse:
    model_name: str
    text: str
    provider: str
    finish_reason: Optional[str] = None
    token_logprobs: Optional[list[TokenLogprob]] = None
    raw: dict = field(default_factory=dict)


# ---- Config loading ----

_MODELS_CONFIG = None


def _load_models_config() -> dict:
    global _MODELS_CONFIG
    if _MODELS_CONFIG is None:
        with open(Path("configs/models.yaml")) as f:
            _MODELS_CONFIG = yaml.safe_load(f)
    return _MODELS_CONFIG


def get_model_spec(model_name: str) -> dict:
    cfg = _load_models_config()
    if model_name not in cfg["models"]:
        raise KeyError(
            f"Model '{model_name}' not in configs/models.yaml. "
            f"Available: {list(cfg['models'].keys())}"
        )
    return cfg["models"][model_name]


# ---- Groq backend ----

_GROQ_CLIENT = None


def _groq_client():
    global _GROQ_CLIENT
    if _GROQ_CLIENT is None:
        from groq import Groq
        key = os.environ.get("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY not set in environment / .env")
        _GROQ_CLIENT = Groq(api_key=key)
    return _GROQ_CLIENT


def _parse_retry_wait(error_message: str) -> float:
    """Extract suggested wait seconds from a Groq 429 message."""
    m = re.search(r"try again in ([\d.]+)s", error_message)
    if m:
        return float(m.group(1))
    return DEFAULT_BACKOFF_SECONDS


def _call_groq(
    model_name: str,
    spec: dict,
    messages: list[dict],
    temperature: float,
    max_tokens: int,
    seed: Optional[int],
    want_logprobs: bool,
) -> ModelResponse:
    from groq import RateLimitError, APIError

    client = _groq_client()
    kwargs = dict(
        model=spec["groq_model_id"],
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if seed is not None:
        kwargs["seed"] = seed
    if want_logprobs:
        kwargs["logprobs"] = True

    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.chat.completions.create(**kwargs)
            choice = resp.choices[0]
            text = choice.message.content or ""
            logprobs = None
            if want_logprobs and getattr(choice, "logprobs", None):
                content_lp = getattr(choice.logprobs, "content", None)
                if content_lp:
                    logprobs = [
                        TokenLogprob(token=lp.token, logprob=lp.logprob)
                        for lp in content_lp
                    ]
            return ModelResponse(
                model_name=model_name,
                text=text,
                provider="groq",
                finish_reason=choice.finish_reason,
                token_logprobs=logprobs,
                raw={"id": getattr(resp, "id", None)},
            )
        except RateLimitError as e:
            last_err = e
            wait = _parse_retry_wait(str(e)) + BACKOFF_PADDING
            print(f"    [rate limit] {model_name}: waiting {wait:.1f}s "
                  f"(attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(wait)
        except APIError as e:
            # Transient server errors: brief backoff then retry
            last_err = e
            wait = DEFAULT_BACKOFF_SECONDS
            print(f"    [api error] {model_name}: {e}; waiting {wait:.1f}s "
                  f"(attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(wait)

    raise RuntimeError(
        f"Groq call for {model_name} failed after {MAX_RETRIES} retries. "
        f"Last error: {last_err}"
    )


# ---- Ollama backend ----

def _call_ollama(
    model_name: str,
    spec: dict,
    messages: list[dict],
    temperature: float,
    max_tokens: int,
    seed: Optional[int],
    want_logprobs: bool,
) -> ModelResponse:
    payload = {
        "model": spec["ollama_model_id"],
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    if seed is not None:
        payload["options"]["seed"] = seed

    r = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json=payload,
        timeout=600,
    )
    r.raise_for_status()
    data = r.json()
    text = data.get("message", {}).get("content", "")
    return ModelResponse(
        model_name=model_name,
        text=text,
        provider="ollama",
        finish_reason=data.get("done_reason"),
        token_logprobs=None,
        raw={"total_duration": data.get("total_duration")},
    )


# ---- Public interface ----

def call_model(
    model_name: str,
    messages: list[dict],
    temperature: float = 0.0,
    max_tokens: int = 1024,
    seed: Optional[int] = None,
    want_logprobs: bool = False,
) -> ModelResponse:
    spec = get_model_spec(model_name)
    provider = spec["provider"]
    if provider == "groq":
        return _call_groq(
            model_name, spec, messages, temperature,
            max_tokens, seed, want_logprobs,
        )
    elif provider == "ollama":
        return _call_ollama(
            model_name, spec, messages, temperature,
            max_tokens, seed, want_logprobs,
        )
    else:
        raise ValueError(f"Unknown provider '{provider}' for {model_name}")
