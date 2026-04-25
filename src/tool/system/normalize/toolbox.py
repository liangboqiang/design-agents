from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from protocol.types import ToolSpec


class NormalizeToolsToolbox:
    toolbox_name = "normalize"
    tags = ("governance", "normalize")

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime

    def spawn(self, workspace_root: Path) -> "NormalizeToolsToolbox":
        return NormalizeToolsToolbox(workspace_root=workspace_root)

    def tool_specs(self) -> Iterable[ToolSpec]:
        return [
            ToolSpec(
                "governance.normalize_tool_result",
                "Normalize tool result",
                "Normalize an arbitrary tool result into a compact JSON payload.",
                {"type": "object", "properties": {"result": {}}, "required": ["result"]},
                lambda args: json.dumps({"result": args["result"]}, ensure_ascii=False, indent=2),
                self.toolbox_name,
                tags=("governance", "normalize"),
            )
        ]
