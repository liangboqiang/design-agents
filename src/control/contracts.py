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
    fault_boundary: Any
    emit_event: Any
    active_skill_id: Any
    history: Any
    max_steps: int
    model_name: str
    assemble_surface: Any
    build_system_prompt: Any
    build_messages: Any
    complete_model: Any
    parse_reply: Any
    dispatch_action: Any
    normalize_tool_result: Any
    record_audit: Any
