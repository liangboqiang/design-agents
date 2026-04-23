from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from schemas.action import ActionSpec
from tool.indexes.toolbox_registry import Toolbox


class InspectToolsToolbox(Toolbox):
    toolbox_name = "inspect_tools"
    tags = ("governance", "surface")

    def spawn(self, workspace_root: Path) -> "InspectToolsToolbox":
        return InspectToolsToolbox(workspace_root=workspace_root)

    def action_specs(self) -> Iterable[ActionSpec]:
        return [
            ActionSpec(
                "governance.inspect_tool_surface",
                "Inspect tool surface",
                "Describe the currently visible tool/action surface.",
                {"type": "object", "properties": {}},
                lambda args: self._inspect(),
                self.toolbox_name,
                tags=("governance", "inspect"),
            )
        ]

    def _inspect(self) -> str:
        if self.engine is None:
            return json.dumps({"visible_actions": []}, ensure_ascii=False, indent=2)
        surface = self.engine.last_surface_snapshot
        if surface is None:
            return json.dumps({"visible_actions": []}, ensure_ascii=False, indent=2)
        return json.dumps(
            {
                "visible_toolboxes": surface.visible_toolboxes,
                "visible_actions": [spec.action_id for spec in surface.visible_actions],
                "activated_skill_ids": surface.activated_skill_ids,
            },
            ensure_ascii=False,
            indent=2,
        )
