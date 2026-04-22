from __future__ import annotations

from schemas.action import ActionSpec

from .base import Capability


class SubagentCapability(Capability):
    capability_name = "subagent"

    def action_specs(self):
        return [
            ActionSpec(
                "subagent.ask",
                "Delegate to subagent",
                "Delegate a subtask to a child engine and return the result.",
                {
                    "type": "object",
                    "properties": {"prompt": {"type": "string"}, "skill": {"type": "string"}, "enhancements": {"type": "array"}},
                    "required": ["prompt"],
                },
                lambda args: self.ask(
                    args["prompt"],
                    args.get("skill"),
                    [str(item) for item in args.get("enhancements") or []],
                ),
                "capability.subagent",
            )
        ]

    def ask(self, prompt: str, skill: str | None, enhancements: list[str]) -> str:
        child = self.engine.spawn_child(
            skill=skill,
            enhancements=enhancements or self.engine.enhancement_names,
            role_name="subagent",
        )
        return child.chat(prompt)

