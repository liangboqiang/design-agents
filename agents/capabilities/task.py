from __future__ import annotations

import json
from pathlib import Path

from agents.capabilities.base import Capability
from agents.core.models import ActionSpec


class TaskCapability(Capability):
    capability_name = "task"

    def bind(self, engine) -> None:
        super().bind(engine)
        self.tasks_dir = engine.paths.state_dir / "tasks"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def _next_id(self) -> int:
        ids = [int(path.stem.split("_")[-1]) for path in self.tasks_dir.glob("task_*.json")]
        return (max(ids) if ids else 0) + 1

    def _task_path(self, task_id: int) -> Path:
        return self.tasks_dir / f"task_{task_id}.json"

    def _task_name(self, task_id: int) -> str:
        return f"tasks/task_{task_id}.json"

    def _load(self, task_id: int) -> dict:
        payload = self.engine.read_state_json(self._task_name(task_id), None)
        if payload is None:
            raise FileNotFoundError(f"Unknown task {task_id}")
        return payload

    def _save(self, payload: dict) -> None:
        self.engine.write_state_json(self._task_name(int(payload["id"])), payload)

    def _clear_dependency(self, completed_id: int) -> None:
        for path in self.tasks_dir.glob("task_*.json"):
            task_id = int(path.stem.split("_")[-1])
            task = self._load(task_id)
            if completed_id in task.get("blocked_by", []):
                task["blocked_by"].remove(completed_id)
                self._save(task)

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
                {
                    "type": "object",
                    "properties": {"task_id": {"type": "integer"}},
                    "required": ["task_id"],
                },
                lambda args: json.dumps(self._load(args["task_id"]), ensure_ascii=False, indent=2),
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
        payload = {
            "id": self._next_id(),
            "subject": subject,
            "description": description,
            "status": "pending",
            "owner": "",
            "blocked_by": blocked_by,
        }
        self._save(payload)
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def update(
        self,
        task_id: int,
        status: str | None,
        owner: str | None,
        add_blocked_by: list[int],
        remove_blocked_by: list[int],
    ) -> str:
        payload = self._load(task_id)
        if status:
            payload["status"] = status
            if status == "completed":
                self._clear_dependency(task_id)
        if owner is not None:
            payload["owner"] = owner
        if add_blocked_by:
            payload["blocked_by"] = sorted(set(payload.get("blocked_by", []) + add_blocked_by))
        if remove_blocked_by:
            payload["blocked_by"] = [
                item for item in payload.get("blocked_by", []) if item not in remove_blocked_by
            ]
        self._save(payload)
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def claim(self, task_id: int, owner: str) -> str:
        payload = self._load(task_id)
        if payload.get("owner"):
            raise ValueError(f"Task {task_id} already owned by {payload['owner']}")
        if payload.get("blocked_by"):
            raise ValueError(f"Task {task_id} is blocked by {payload['blocked_by']}")
        payload["owner"] = owner
        payload["status"] = "in_progress"
        self._save(payload)
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def list_all(self) -> str:
        rows = [self._load(int(path.stem.split("_")[-1])) for path in sorted(self.tasks_dir.glob("task_*.json"))]
        return json.dumps(rows, ensure_ascii=False, indent=2)

    def unclaimed_tasks(self) -> list[dict]:
        rows = [self._load(int(path.stem.split("_")[-1])) for path in sorted(self.tasks_dir.glob("task_*.json"))]
        return [
            row
            for row in rows
            if row.get("status") == "pending" and not row.get("owner") and not row.get("blocked_by")
        ]

    def state_fragments(self) -> list[str]:
        rows = [self._load(int(path.stem.split("_")[-1])) for path in sorted(self.tasks_dir.glob("task_*.json"))]
        if not rows:
            return ["tasks: (none)"]
        summary = "\n".join(
            f"- #{row['id']} {row['subject']} | {row['status']} | owner={row['owner'] or '-'} | blocked_by={row.get('blocked_by', [])}"
            for row in rows[:10]
        )
        return [f"tasks:\n{summary}"]
