from __future__ import annotations

import json

from schemas.action import ActionSpec

from .base import Capability


class TaskCapability(Capability):
    capability_name = "task"

    def action_specs(self):
        return [
            ActionSpec(
                "task.create",
                "Create task",
                "Create a persisted task.",
                {
                    "type": "object",
                    "properties": {
                        "subject": {"type": "string"},
                        "description": {"type": "string"},
                        "blocked_by": {"type": "array"},
                    },
                    "required": ["subject"],
                },
                lambda args: self.create(
                    args["subject"],
                    args.get("description", ""),
                    args.get("blocked_by") or [],
                ),
                "capability.task",
            ),
            ActionSpec(
                "task.update",
                "Update task",
                "Update task status, owner, or dependencies.",
                {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "integer"},
                        "status": {"type": "string"},
                        "owner": {"type": "string"},
                        "add_blocked_by": {"type": "array"},
                        "remove_blocked_by": {"type": "array"},
                    },
                    "required": ["task_id"],
                },
                lambda args: self.update(
                    args["task_id"],
                    args.get("status"),
                    args.get("owner"),
                    args.get("add_blocked_by") or [],
                    args.get("remove_blocked_by") or [],
                ),
                "capability.task",
            ),
            ActionSpec(
                "task.list",
                "List tasks",
                "List all tasks.",
                {"type": "object", "properties": {}},
                lambda args: self.list_all(),
                "capability.task",
            ),
            ActionSpec(
                "task.get",
                "Get task",
                "Get a single task.",
                {"type": "object", "properties": {"task_id": {"type": "integer"}}, "required": ["task_id"]},
                lambda args: json.dumps(self.engine.session.tasks.get(args["task_id"]), ensure_ascii=False, indent=2),
                "capability.task",
            ),
            ActionSpec(
                "task.claim",
                "Claim task",
                "Claim an unowned task.",
                {
                    "type": "object",
                    "properties": {"task_id": {"type": "integer"}, "owner": {"type": "string"}},
                    "required": ["task_id", "owner"],
                },
                lambda args: self.claim(args["task_id"], args["owner"]),
                "capability.task",
            ),
        ]

    def create(self, subject: str, description: str, blocked_by: list[int]) -> str:
        payload = self.engine.session.tasks.create(subject, description, blocked_by)
        if blocked_by:
            self.engine.events.emit("task.blocked", task_id=payload["id"], blocked_by=blocked_by)
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def update(
        self,
        task_id: int,
        status: str | None,
        owner: str | None,
        add_blocked_by: list[int],
        remove_blocked_by: list[int],
    ) -> str:
        payload = self.engine.session.tasks.update(
            task_id,
            status=status,
            owner=owner,
            add_blocked_by=add_blocked_by,
            remove_blocked_by=remove_blocked_by,
        )
        if payload.get("blocked_by"):
            self.engine.events.emit("task.blocked", task_id=task_id, blocked_by=payload["blocked_by"])
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def claim(self, task_id: int, owner: str) -> str:
        payload = self.engine.session.tasks.claim(task_id, owner)
        self.engine.events.emit("task.claimed", task_id=task_id, owner=owner)
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def list_all(self) -> str:
        return json.dumps(self.engine.session.tasks.list_all(), ensure_ascii=False, indent=2)

    def unclaimed_tasks(self) -> list[dict]:
        return self.engine.session.tasks.unclaimed()

    def state_fragments(self) -> list[str]:
        rows = self.engine.session.tasks.list_all()
        if not rows:
            return ["tasks: (none)"]
        summary = "\n".join(
            f"- #{row['id']} {row['subject']} | {row['status']} | owner={row['owner'] or '-'} | blocked_by={row.get('blocked_by', [])}"
            for row in rows[:10]
        )
        return [f"tasks:\n{summary}"]

