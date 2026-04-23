from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class PromptPacket:
    system_prompt: str
    messages: list[dict] = field(default_factory=list)
