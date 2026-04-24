from __future__ import annotations

from schemas.action import ActionSpec

from .base import Capability


class AutonomyCapability(Capability):
    capability_name = "autonomy"

    def action_specs(self):
        return [
            ActionSpec(
                "autonomy.claim_next_task",
                "Claim next task",
                "Claim the next unowned task.",
                {"type": "object", "properties": {"owner": {"type": "string"}}, "required": ["owner"]},
                lambda args: self.claim_next(args["owner"]),
                "capability.autonomy",
            )
        ]

    def claim_next(self, owner: str) -> str:
        task_cap = self.capability("task")
        if task_cap is None:
            return "Task capability not enabled."
        unclaimed = task_cap.unclaimed_tasks()
        if not unclaimed:
            return "No unclaimed tasks."
        return task_cap.claim(int(unclaimed[0]["id"]), owner)

    def idle_tick(self) -> str:
        return self.claim_next(self.runtime.engine_id)

