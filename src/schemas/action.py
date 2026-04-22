from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

JsonDict = dict[str, Any]
ActionExecutor = Callable[[JsonDict], str]


@dataclass(slots=True)
class ActionSpec:
    action_id: str
    title: str
    description: str
    input_schema: JsonDict
    executor: ActionExecutor
    source: str
    detail: str = ""
    visible: bool = True
    tags: tuple[str, ...] = ()


@dataclass(slots=True)
class ToolCall:
    call_id: str
    action: str
    arguments: JsonDict


@dataclass(slots=True)
class LLMResponse:
    assistant_message: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw_text: str = ""

