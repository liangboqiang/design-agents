from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    @abstractmethod
    def complete(self, system_prompt: str, messages: list[dict]) -> str:
        raise NotImplementedError
