from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL = "gpt-4.1-mini"

DEFAULT_BASE_URLS: dict[str, str | None] = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com",
    "mock": None,
}


@dataclass(frozen=True, slots=True)
class LLMConfig:
    provider: str
    model: str
    api_key: str | None
    base_url: str | None


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def resolve_provider(provider: str | None = None) -> str:
    value = _clean(provider) or _clean(os.getenv("DESIGN_AGENTS_PROVIDER")) or DEFAULT_PROVIDER
    normalized = value.lower()
    if normalized not in DEFAULT_BASE_URLS:
        raise ValueError(f"Unsupported provider: {normalized}")
    return normalized


def resolve_model(model: str | None = None) -> str:
    return _clean(model) or _clean(os.getenv("DESIGN_AGENTS_MODEL")) or DEFAULT_MODEL


def resolve_api_key(api_key: str | None = None, *, provider: str | None = None) -> str | None:
    normalized_provider = resolve_provider(provider)
    value = (
        _clean(api_key)
        or _clean(os.getenv("DESIGN_AGENTS_API_KEY"))
        or _clean(os.getenv(f"{normalized_provider.upper()}_API_KEY"))
    )
    if normalized_provider == "mock":
        return value
    if not value:
        raise ValueError(
            f"Missing API key for provider '{normalized_provider}'. "
            "Set DESIGN_AGENTS_API_KEY in .env or pass api_key explicitly."
        )
    return value


def resolve_base_url(base_url: str | None = None, *, provider: str | None = None) -> str | None:
    normalized_provider = resolve_provider(provider)
    if normalized_provider == "mock":
        return None
    value = (
        _clean(base_url)
        or _clean(os.getenv("DESIGN_AGENTS_BASE_URL"))
        or _clean(os.getenv(f"{normalized_provider.upper()}_BASE_URL"))
        or DEFAULT_BASE_URLS[normalized_provider]
    )
    if value is None:
        return None
    return value.rstrip("/")


def resolve_llm_config(
    *,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> LLMConfig:
    normalized_provider = resolve_provider(provider)
    return LLMConfig(
        provider=normalized_provider,
        model=resolve_model(model),
        api_key=resolve_api_key(api_key, provider=normalized_provider),
        base_url=resolve_base_url(base_url, provider=normalized_provider),
    )
