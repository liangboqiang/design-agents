from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from schemas.action import ActionSpec
from tool.indexes.toolbox_registry import Toolbox


class NormalizeToolsToolbox(Toolbox):
    toolbox_name = "normalize_tools"
    tags = ("governance", "normalize")

    def spawn(self, workspace_root: Path) -> "NormalizeToolsToolbox":
        return NormalizeToolsToolbox(workspace_root=workspace_root)

    def action_specs(self) -> Iterable[ActionSpec]:
        return [
            ActionSpec(
                "governance.normalize_tool_result",
                "Normalize tool result",
                "Normalize an arbitrary tool result into a compact JSON payload.",
                {
                    "type": "object",
                    "properties": {"result": {}},
                    "required": ["result"],
                },
                lambda args: json.dumps({"result": args["result"]}, ensure_ascii=False, indent=2),
                self.toolbox_name,
                tags=("governance", "normalize"),
            )
        ]
