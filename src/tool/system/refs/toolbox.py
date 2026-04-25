from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from protocol.types import ToolSpec


class LoadRefsToolbox:
    toolbox_name = "refs"
    tags = ("governance", "refs")

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime

    def spawn(self, workspace_root: Path) -> "LoadRefsToolbox":
        return LoadRefsToolbox(workspace_root=workspace_root)

    def tool_specs(self) -> Iterable[ToolSpec]:
        return [
            ToolSpec(
                "governance.load_refs",
                "Load refs",
                "Inspect the currently activated skill refs closure.",
                {"type": "object", "properties": {}},
                lambda args: self._load_refs(),
                self.toolbox_name,
                tags=("governance", "refs"),
            )
        ]

    def _load_refs(self) -> str:
        if self.runtime is None:
            return json.dumps({"refs": []}, ensure_ascii=False, indent=2)
        return json.dumps(
            {"active_skill": self.runtime.skill_state.active_skill_id, "activated_skill_ids": self.runtime.skill_state.activated_skill_ids()},
            ensure_ascii=False,
            indent=2,
        )
