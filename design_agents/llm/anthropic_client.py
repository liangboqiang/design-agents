from __future__ import annotations

import requests

from .base import BaseLLMClient
from .coding_plan import resolve_anthropic_base_url, resolve_coding_plan_api_key


class AnthropicClient(BaseLLMClient):
    def __init__(self, model: str, api_key: str | None, base_url: str | None = None):
        self.model = model
        self.api_key = resolve_coding_plan_api_key(api_key)
        self.base_url = resolve_anthropic_base_url(base_url)
        self.url = f"{self.base_url}/v1/messages"

    def complete(self, system_prompt: str, messages: list[dict]) -> str:
        payload = {
            "model": self.model,
            "max_tokens": 4000,
            "temperature": 0.2,
            "system": system_prompt,
            "messages": messages,
        }
        response = requests.post(
            self.url,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
            timeout=180,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            detail = ""
            try:
                payload = response.json()
                detail = payload.get("error", {}).get("message", "")
            except Exception:
                detail = response.text.strip()
            if response.status_code == 401:
                raise ValueError(
                    "Coding Plan Anthropic authentication failed (401 Unauthorized). "
                    "Check that the API key starts with 'sk-sp-' and that the "
                    "Base URL is the Coding Plan Anthropic endpoint."
                    + (f" Detail: {detail}" if detail else "")
                ) from exc
            raise ValueError(
                f"Coding Plan Anthropic request failed with status {response.status_code}."
                + (f" Detail: {detail}" if detail else "")
            ) from exc
        data = response.json()
        return "\n".join(
            part.get("text", "")
            for part in data.get("content", [])
            if part.get("type") == "text"
        )
