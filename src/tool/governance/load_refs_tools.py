from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from schemas.action import ActionSpec
from tool.indexes.toolbox_registry import Toolbox


class LoadRefsToolbox(Toolbox):
    toolbox_name = "load_refs"
    tags = ("governance", "refs")

    def spawn(self, workspace_root: Path) -> "LoadRefsToolbox":
        return LoadRefsToolbox(workspace_root=workspace_root)

    def action_specs(self) -> Iterable[ActionSpec]:
        return [
            ActionSpec(
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
        if self.engine is None:
            return json.dumps({"refs": []}, ensure_ascii=False, indent=2)
        return json.dumps(
            {
                "active_skill": self.engine.skill_state.active_skill_id,
                "activated_skill_ids": self.engine.skill_state.activated_skill_ids(),
            },
            ensure_ascii=False,
            indent=2,
        )
