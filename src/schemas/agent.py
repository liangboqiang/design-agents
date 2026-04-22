from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AgentSpec:
    name: str
    root_skill: str
    description: str = ""
    toolboxes: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    llm: dict[str, Any] = field(default_factory=dict)
    context_policy: dict[str, Any] = field(default_factory=dict)
    source_path: str = ""

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "AgentSpec":
        return cls(
            name=str(payload["name"]),
            root_skill=str(payload["root_skill"]),
            description=str(payload.get("description") or ""),
            toolboxes=[str(item) for item in payload.get("toolboxes") or []],
            capabilities=[str(item) for item in payload.get("capabilities") or []],
            llm=dict(payload.get("llm") or {}),
            context_policy=dict(payload.get("context_policy") or {}),
            source_path=str(payload.get("source_path") or ""),
        )
