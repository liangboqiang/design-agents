from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ContextPacket:
    system_prompt: str
    messages: list[dict] = field(default_factory=list)


# Compatibility alias for older call sites during transition.
PromptPacket = ContextPacket
