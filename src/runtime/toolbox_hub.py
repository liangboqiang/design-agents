from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ToolboxHub:
    tool_index: Any
    toolboxes: list[Any] = field(default_factory=list)

    def names(self) -> list[str]:
        return [str(getattr(toolbox, "toolbox_name", "")) for toolbox in self.toolboxes]
