from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ToolDescriptor:
    tool_id: str
    toolbox_name: str
    title: str
    description: str
    module: str
    tags: list[str] = field(default_factory=list)
    action_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ToolboxDescriptor:
    toolbox_name: str
    module: str
    class_name: str
    discoverable: bool = True
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

