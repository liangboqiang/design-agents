from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class EngineRuntimeState:
    last_surface_snapshot: Any | None = None
    last_fault: Any | None = None
    fault_history: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TurnRuntimePorts:
    lifecycle: Any
    events: Any
    skill_runtime: Any
    session: Any
    settings: Any
    surface_resolver: Any
    context_assembler: Any
    llm: Any
    response_parser: Any
    dispatcher: Any
    normalizer: Any
    audit: Any
    context: Any
    registry: Any
    knowledge_hub: Any
    action_registry: dict[str, Any]
    state: EngineRuntimeState
    failure_sink: Any
    fault_boundary: Any


TurnRuntimeState = EngineRuntimeState
