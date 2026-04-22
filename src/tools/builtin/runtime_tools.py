from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from schemas.action import ActionSpec
from tools.indexes.toolbox_registry import Toolbox


class RuntimeToolbox(Toolbox):
    toolbox_name = "runtime_tools"
    tags = ("builtin", "runtime")

    def spawn(self, workspace_root: Path) -> "RuntimeToolbox":
        return RuntimeToolbox(workspace_root=workspace_root)

    def action_specs(self) -> Iterable[ActionSpec]:
        return [
            ActionSpec(
                "runtime_tools.describe_workspace",
                "Describe workspace",
                "Describe the current runtime workspace root.",
                {"type": "object", "properties": {}},
                lambda args: str(self.workspace_root or ""),
                self.toolbox_name,
                tags=("runtime", "workspace"),
            ),
            ActionSpec(
                "runtime_tools.describe_session",
                "Describe session",
                "Describe the current session runtime bindings.",
                {"type": "object", "properties": {}},
                lambda args: self._describe_session(),
                self.toolbox_name,
                tags=("runtime", "session"),
            ),
        ]

    def _describe_session(self) -> str:
        if self.engine is None:
            return json.dumps({"workspace_root": str(self.workspace_root or "")}, ensure_ascii=False, indent=2)
        return json.dumps(
            {
                "engine_id": self.engine.engine_id,
                "agent_name": self.engine.agent_spec.name,
                "workspace_root": str(self.engine.session.workspace_root),
                "user_id": self.engine.settings.user_id,
                "conversation_id": self.engine.settings.conversation_id,
                "task_id": self.engine.settings.task_id,
            },
            ensure_ascii=False,
            indent=2,
        )

