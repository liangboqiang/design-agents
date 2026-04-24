from __future__ import annotations

import json

from schemas.action import ActionSpec


class TurnPolicy:
    def __init__(self, *, registry, skill_state, context, events, action_registry):  # noqa: ANN001
        self.registry = registry
        self.skill_state = skill_state
        self.context = context
        self.events = events
        self.action_registry = action_registry

    def inspect_skill(self, skill: str) -> str:
        target = self.skill_state.resolve_skill_alias(skill)
        return self.registry.get_skill(target).markdown_path.read_text(encoding="utf-8")

    def inspect_action(self, action: str) -> str:
        spec = self.action_registry[action]
        return json.dumps(
            {
                "action": spec.action_id,
                "title": spec.title,
                "description": spec.description,
                "input_schema": spec.input_schema,
                "source": spec.source,
                "detail": spec.detail,
            },
            ensure_ascii=False,
            indent=2,
        )

    def list_child_skills(self) -> str:
        rows = self.registry.list_children_cards(self.skill_state.active_skill_id)
        return json.dumps(
            [{"skill": skill_id, "summary": summary} for skill_id, summary in rows],
            ensure_ascii=False,
            indent=2,
        )

    def enter_skill(self, skill: str) -> str:
        result = self.skill_state.enter_skill(skill)
        self.context.active_skill_id = self.skill_state.active_skill_id
        self.events.emit("skill.entered", skill=self.skill_state.active_skill_id)
        return result


def build_control_action_specs(control) -> list[ActionSpec]:  # noqa: ANN001
    return [
        ActionSpec(
            "engine.inspect_skill",
            "Inspect skill",
            "Load the full skill page for a reachable skill.",
            {"type": "object", "properties": {"skill": {"type": "string"}}, "required": ["skill"]},
            lambda args: control.inspect_skill(args["skill"]),
            "control.turn_policy",
        ),
        ActionSpec(
            "engine.inspect_action",
            "Inspect action",
            "Inspect an action description and input schema.",
            {"type": "object", "properties": {"action": {"type": "string"}}, "required": ["action"]},
            lambda args: control.inspect_action(args["action"]),
            "control.turn_policy",
        ),
        ActionSpec(
            "engine.enter_skill",
            "Enter skill",
            "Switch the active skill.",
            {"type": "object", "properties": {"skill": {"type": "string"}}, "required": ["skill"]},
            lambda args: control.enter_skill(args["skill"]),
            "control.turn_policy",
        ),
        ActionSpec(
            "engine.list_child_skills",
            "List child skills",
            "List direct child skills for the active skill.",
            {"type": "object", "properties": {}},
            lambda args: control.list_child_skills(),
            "control.turn_policy",
        ),
    ]
