from __future__ import annotations

from .anthropic_client import AnthropicClient
from .base import BaseLLMClient
from .config import resolve_api_key, resolve_base_url, resolve_model, resolve_provider
from .mock_client import MockClient
from .openai_client import OpenAIClient


class LLMFactory:
    @staticmethod
    def create(
        provider: str | None,
        model: str | None,
        api_key: str | None,
        base_url: str | None = None,
    ) -> BaseLLMClient:
        resolved_provider = resolve_provider(provider)
        resolved_model = resolve_model(model)
        if resolved_provider == "mock":
            return MockClient(resolved_model)

        resolved_api_key = resolve_api_key(api_key)
        resolved_base_url = resolve_base_url(resolved_provider, base_url)

        if resolved_provider == "openai":
            return OpenAIClient(resolved_model, resolved_api_key or "", resolved_base_url or "")
        if resolved_provider == "anthropic":
            return AnthropicClient(resolved_model, resolved_api_key or "", resolved_base_url or "")
        raise ValueError(f"Unsupported provider: {resolved_provider}")
