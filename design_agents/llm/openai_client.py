from __future__ import annotations

import requests

from .base import BaseLLMClient
from .coding_plan import resolve_coding_plan_api_key, resolve_openai_base_url


class OpenAIClient(BaseLLMClient):
    def __init__(self, model: str, api_key: str | None, base_url: str | None = None):
        self.model = model
        self.api_key = resolve_coding_plan_api_key(api_key)
        self.base_url = resolve_openai_base_url(base_url)
        self.url = f"{self.base_url}/chat/completions"

    def complete(self, system_prompt: str, messages: list[dict]) -> str:
        payload = {
            "model": self.model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system_prompt}, *messages],
        }
        response = requests.post(
            self.url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
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
                    "Coding Plan OpenAI authentication failed (401 Unauthorized). "
                    "Check that the API key starts with 'sk-sp-' and that the "
                    "Base URL is the Coding Plan OpenAI endpoint."
                    + (f" Detail: {detail}" if detail else "")
                ) from exc
            raise ValueError(
                f"Coding Plan OpenAI request failed with status {response.status_code}."
                + (f" Detail: {detail}" if detail else "")
            ) from exc
        return response.json()["choices"][0]["message"]["content"]
