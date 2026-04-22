from __future__ import annotations

from schemas.action import ActionSpec
from schemas.tool import ToolDescriptor


class ToolIndex:
    def __init__(self):
        self.descriptors: dict[str, ToolDescriptor] = {}

    def register_action(self, toolbox_name: str, spec: ActionSpec) -> None:
        self.descriptors[spec.action_id] = ToolDescriptor(
            tool_id=spec.action_id,
            toolbox_name=toolbox_name,
            title=spec.title,
            description=spec.description,
            module=spec.source,
            tags=list(spec.tags),
            action_ids=[spec.action_id],
        )

    def register_toolbox_actions(self, toolbox_name: str, specs: list[ActionSpec]) -> None:
        for spec in specs:
            self.register_action(toolbox_name, spec)

    def get(self, tool_id: str) -> ToolDescriptor:
        return self.descriptors[tool_id]

    def list_all(self) -> list[ToolDescriptor]:
        return [self.descriptors[key] for key in sorted(self.descriptors)]

