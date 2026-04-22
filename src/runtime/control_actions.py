from __future__ import annotations

from schemas.action import ActionSpec


def build_control_action_specs(control) -> list[ActionSpec]:  # noqa: ANN001
    return [
        ActionSpec(
            "engine.inspect_skill",
            "Inspect skill",
            "Load the full SKILL.md for a reachable skill.",
            {"type": "object", "properties": {"skill": {"type": "string"}}, "required": ["skill"]},
            lambda args: control.inspect_skill(args["skill"]),
            "runtime.engine",
        ),
        ActionSpec(
            "engine.inspect_action",
            "Inspect action",
            "Inspect an action description and input schema.",
            {"type": "object", "properties": {"action": {"type": "string"}}, "required": ["action"]},
            lambda args: control.inspect_action(args["action"]),
            "runtime.engine",
        ),
        ActionSpec(
            "engine.enter_skill",
            "Enter skill",
            "Switch the active skill.",
            {"type": "object", "properties": {"skill": {"type": "string"}}, "required": ["skill"]},
            lambda args: control.enter_skill(args["skill"]),
            "runtime.engine",
        ),
        ActionSpec(
            "engine.list_child_skills",
            "List child skills",
            "List direct child skills for the active skill.",
            {"type": "object", "properties": {}},
            lambda args: control.list_child_skills(),
            "runtime.engine",
        ),
    ]
