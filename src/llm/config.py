from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from .errors import LLMConfigurationError


load_dotenv(override=False)

ENV_PROVIDER = "DESIGN_AGENTS_PROVIDER"
ENV_MODEL = "DESIGN_AGENTS_MODEL"
ENV_API_KEY = "DESIGN_AGENTS_API_KEY"
ENV_BASE_URL = "DESIGN_AGENTS_BASE_URL"

DEFAULT_PROVIDER = "mock"
DEFAULT_MODEL = "mock"


@dataclass(frozen=True, slots=True)
class LLMConfig:
    provider: str
    model: str
    api_key: str | None
    base_url: str | None


def resolve_llm_config(
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> LLMConfig:
    resolved_provider = (provider or os.getenv(ENV_PROVIDER) or DEFAULT_PROVIDER).strip().lower()
    if resolved_provider not in {"openai", "anthropic", "mock"}:
        raise LLMConfigurationError(f"Unsupported provider: {resolved_provider}")

    raw_model = (model or os.getenv(ENV_MODEL) or "").strip()
    resolved_model = raw_model or (DEFAULT_MODEL if resolved_provider == "mock" else "")
    if not resolved_model:
        raise LLMConfigurationError(f"{resolved_provider} provider requires model.")

    if resolved_provider == "mock":
        return LLMConfig("mock", resolved_model, None, None)

    resolved_api_key = (api_key or os.getenv(ENV_API_KEY) or "").strip() or None
    resolved_base_url = (base_url or os.getenv(ENV_BASE_URL) or "").strip().rstrip("/") or None

    if not resolved_api_key:
        raise LLMConfigurationError(f"{resolved_provider} provider requires api_key.")
    if not resolved_base_url:
        raise LLMConfigurationError(f"{resolved_provider} provider requires base_url.")

    return LLMConfig(
        provider=resolved_provider,
        model=resolved_model,
        api_key=resolved_api_key,
        base_url=resolved_base_url,
    )

