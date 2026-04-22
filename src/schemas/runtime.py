from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .action import ActionSpec


@dataclass(slots=True)
class RuntimePaths:
    root: Path
    history_dir: Path
    state_dir: Path
    workspace_dir: Path
    inbox_dir: Path
    logs_dir: Path
    attachments_dir: Path


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
    max_prompt_chars: int = 18_000


@dataclass(slots=True)
class EngineContext:
    engine_id: str
    root_skill_id: str
    active_skill_id: str
    settings: EngineSettings
    paths: RuntimePaths
    agent_name: str = "ad-hoc"


@dataclass(slots=True)
class SurfaceSnapshot:
    visible_actions: list[ActionSpec]
    visible_skills: list[tuple[str, str]]
    visible_toolboxes: list[str]
    activated_skill_ids: list[str] = field(default_factory=list)
    governance_notes: list[str] = field(default_factory=list)
