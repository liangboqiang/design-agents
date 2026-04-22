from __future__ import annotations

from .anthropic_client import AnthropicClient
from .base import BaseLLMClient
from .mock_client import MockClient
from .openai_client import OpenAIClient


class LLMFactory:
    @staticmethod
    def create(
        provider: str,
        model: str,
        api_key: str | None,
        base_url: str | None = None,
    ) -> BaseLLMClient:
        provider = provider.lower().strip()
        if provider == "openai":
            return OpenAIClient(model, api_key, base_url=base_url)
        if provider == "anthropic":
            return AnthropicClient(model, api_key, base_url=base_url)
        if provider == "mock":
            return MockClient(model)
        raise ValueError(f"Unsupported provider: {provider}")
