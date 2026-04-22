from __future__ import annotations

import os


DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL = "qwen3-coder-plus"
DEFAULT_OPENAI_BASE_URL = "https://coding-intl.dashscope.aliyuncs.com/v1"
DEFAULT_ANTHROPIC_BASE_URL = "https://coding-intl.dashscope.aliyuncs.com/apps/anthropic"

ENV_PROVIDER = "DESIGN_AGENTS_PROVIDER"
ENV_MODEL = "DESIGN_AGENTS_MODEL"
ENV_API_KEY = "DESIGN_AGENTS_API_KEY"
ENV_BASE_URL = "DESIGN_AGENTS_BASE_URL"


def resolve_provider(provider: str | None) -> str:
    value = (provider or os.getenv(ENV_PROVIDER) or DEFAULT_PROVIDER).strip().lower()
    if value not in {"openai", "anthropic", "mock"}:
        raise ValueError(f"Unsupported provider: {value}")
    return value


def resolve_model(model: str | None) -> str:
    value = (model or os.getenv(ENV_MODEL) or DEFAULT_MODEL).strip()
    if not value:
        raise ValueError("Model is required.")
    return value


def resolve_api_key(api_key: str | None) -> str | None:
    value = (api_key or os.getenv(ENV_API_KEY) or "").strip()
    return value or None


def default_base_url(provider: str) -> str | None:
    if provider == "openai":
        return DEFAULT_OPENAI_BASE_URL
    if provider == "anthropic":
        return DEFAULT_ANTHROPIC_BASE_URL
    return None


def resolve_base_url(provider: str, base_url: str | None) -> str | None:
    value = (base_url or os.getenv(ENV_BASE_URL) or default_base_url(provider) or "").strip().rstrip("/")
    return value or None
