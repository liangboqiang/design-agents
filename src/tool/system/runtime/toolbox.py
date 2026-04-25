from __future__ import annotations

from pathlib import Path
from typing import Iterable

from protocol.types import ToolSpec
from .ops import EngineOps


class EngineToolbox:
    toolbox_name = "engine"
    discoverable = False
    tags = ("engine", "runtime")

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime

    def spawn(self, workspace_root: Path) -> "EngineToolbox":
        return EngineToolbox(workspace_root=workspace_root)

    def tool_specs(self) -> Iterable[ToolSpec]:
        return [
            ToolSpec(
                "engine.inspect_skill",
                "Inspect skill",
                "Load the full page for a reachable skill.",
                {"type": "object", "properties": {"skill": {"type": "string"}}, "required": ["skill"]},
                lambda args: self._ops().inspect_skill(args["skill"]),
                self.toolbox_name,
            ),
            ToolSpec(
                "engine.inspect_tool",
                "Inspect tool",
                "Inspect one visible tool description and schema.",
                {"type": "object", "properties": {"tool": {"type": "string"}}, "required": ["tool"]},
                lambda args: self._ops().inspect_tool(args["tool"]),
                self.toolbox_name,
            ),
            ToolSpec(
                "engine.enter_skill",
                "Enter skill",
                "Switch the active skill.",
                {"type": "object", "properties": {"skill": {"type": "string"}}, "required": ["skill"]},
                lambda args: self._ops().enter_skill(args["skill"]),
                self.toolbox_name,
            ),
            ToolSpec(
                "engine.list_child_skills",
                "List child skills",
                "List direct child skills for the active skill.",
                {"type": "object", "properties": {}},
                lambda args: self._ops().list_child_skills(),
                self.toolbox_name,
            ),
        ]

    def _ops(self) -> EngineOps:
        if self.runtime is None:
            raise RuntimeError("EngineToolbox runtime not bound yet.")
        return EngineOps(
            registry=self.runtime.registry,
            skill_state=self.runtime.skill_state,
            context=self.runtime.context,
            events=self.runtime.events,
            tool_registry=self.runtime.runtime_state.tool_registry,
        )
