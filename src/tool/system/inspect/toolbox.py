from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from protocol.types import ToolSpec


class InspectToolsToolbox:
    toolbox_name = "inspect"
    tags = ("governance", "surface")

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime

    def spawn(self, workspace_root: Path) -> "InspectToolsToolbox":
        return InspectToolsToolbox(workspace_root=workspace_root)

    def tool_specs(self) -> Iterable[ToolSpec]:
        return [
            ToolSpec(
                "governance.inspect_tool_surface",
                "Inspect tool surface",
                "Describe the currently visible tool surface.",
                {"type": "object", "properties": {}},
                lambda args: self._inspect(),
                self.toolbox_name,
                tags=("governance", "inspect"),
            )
        ]

    def _inspect(self) -> str:
        if self.runtime is None:
            return json.dumps({"visible_tools": []}, ensure_ascii=False, indent=2)
        surface = self.runtime.runtime_state.last_surface_snapshot
        if surface is None:
            return json.dumps({"visible_tools": []}, ensure_ascii=False, indent=2)
        return json.dumps(
            {
                "visible_toolboxes": surface.visible_toolboxes,
                "visible_tools": [spec.tool_id for spec in surface.visible_tools],
                "activated_skill_ids": surface.activated_skill_ids,
                "activated_tools": surface.activated_tools,
            },
            ensure_ascii=False,
            indent=2,
        )
