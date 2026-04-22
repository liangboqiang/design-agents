from __future__ import annotations

import os


CODING_PLAN_OPENAI_BASE_URL = "https://coding-intl.dashscope.aliyuncs.com/v1"
CODING_PLAN_ANTHROPIC_BASE_URL = "https://coding-intl.dashscope.aliyuncs.com/apps/anthropic"
DEFAULT_CODING_PLAN_MODEL = "qwen3-coder-plus"


def resolve_coding_plan_api_key(api_key: str | None) -> str:
    value = (api_key or os.getenv("CODING_PLAN_API_KEY") or "").strip()
    if not value:
        raise ValueError(
            "Coding Plan API key missing. Pass --api-key or set CODING_PLAN_API_KEY."
        )
    if not value.startswith("sk-sp-"):
        raise ValueError(
            "Coding Plan API key must start with 'sk-sp-'. "
            "Do not mix it with a regular Model Studio key."
        )
    return value


def resolve_openai_base_url(base_url: str | None) -> str:
    value = (
        base_url
        or os.getenv("CODING_PLAN_OPENAI_BASE_URL")
        or CODING_PLAN_OPENAI_BASE_URL
    )
    cleaned = value.strip().rstrip("/")
    if cleaned.endswith("/chat/completions"):
        raise ValueError(
            "Use the Coding Plan OpenAI Base URL, not the final endpoint. "
            "Expected a base URL like "
            "'https://coding-intl.dashscope.aliyuncs.com/v1'."
        )
    return cleaned


def resolve_anthropic_base_url(base_url: str | None) -> str:
    value = (
        base_url
        or os.getenv("CODING_PLAN_ANTHROPIC_BASE_URL")
        or CODING_PLAN_ANTHROPIC_BASE_URL
    )
    cleaned = value.strip().rstrip("/")
    if cleaned.endswith("/messages"):
        raise ValueError(
            "Use the Coding Plan Anthropic Base URL, not the final endpoint. "
            "Expected a base URL like "
            "'https://coding-intl.dashscope.aliyuncs.com/apps/anthropic'."
        )
    return cleaned
