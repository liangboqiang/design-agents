from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

JsonDict = dict[str, Any]


@dataclass(slots=True)
class ActionSpec:
    action_id: str
    title: str
    description: str
    input_schema: JsonDict
    executor: Callable[[JsonDict], str]
    source: str
    detail: str = ""
    visible: bool = True


@dataclass(slots=True)
class SkillNode:
    skill_id: str
    name: str
    description: str
    directory: Path
    markdown_path: Path
    markdown_body: str
    frontmatter: JsonDict
    children: list[str] = field(default_factory=list)
    refs: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)


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


@dataclass(slots=True)
class RuntimePaths:
    root: Path
    history_dir: Path
    state_dir: Path
    workspace_dir: Path
    inbox_dir: Path
    logs_dir: Path


@dataclass(slots=True)
class EngineSettings:
    provider: str
    model: str
    api_key: str | None
    base_url: str | None
    user_id: str
    conversation_id: str
    task_id: str
    max_steps: int = 12
    history_keep_turns: int = 24
    auto_compact_threshold: int = 30_000


@dataclass(slots=True)
class EngineContext:
    engine_id: str
    root_skill_id: str
    active_skill_id: str
    settings: EngineSettings
    paths: RuntimePaths
