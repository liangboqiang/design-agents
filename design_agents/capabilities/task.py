from __future__ import annotations

import json
from pathlib import Path

from design_agents.capabilities.base import Capability
from design_agents.core.models import ActionSpec


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

    def _load(self, task_id: int) -> dict:
        return json.loads(self._task_path(task_id).read_text(encoding="utf-8"))

    def _save(self, payload: dict) -> None:
        self._task_path(int(payload["id"])).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _clear_dependency(self, completed_id: int) -> None:
        for path in self.tasks_dir.glob("task_*.json"):
            task = json.loads(path.read_text(encoding="utf-8"))
            if completed_id in task.get("blocked_by", []):
                task["blocked_by"].remove(completed_id)
                path.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")

    def action_specs(self):
        return [
            ActionSpec("task.create", "Create task", "创建持久化任务。", {"type": "object", "properties": {"subject": {"type": "string"}, "description": {"type": "string"}, "blocked_by": {"type": "array"}}, "required": ["subject"]}, lambda args: self.create(args["subject"], args.get("description", ""), args.get("blocked_by") or []), "capability.task"),
            ActionSpec("task.update", "Update task", "更新任务状态、所有者或依赖关系。", {"type": "object", "properties": {"task_id": {"type": "integer"}, "status": {"type": "string"}, "owner": {"type": "string"}, "add_blocked_by": {"type": "array"}, "remove_blocked_by": {"type": "array"}}, "required": ["task_id"]}, lambda args: self.update(args["task_id"], args.get("status"), args.get("owner"), args.get("add_blocked_by") or [], args.get("remove_blocked_by") or []), "capability.task"),
            ActionSpec("task.list", "List tasks", "列出所有任务。", {"type": "object", "properties": {}}, lambda args: self.list_all(), "capability.task"),
            ActionSpec("task.get", "Get task", "查看单个任务详情。", {"type": "object", "properties": {"task_id": {"type": "integer"}}, "required": ["task_id"]}, lambda args: json.dumps(self._load(args["task_id"]), ensure_ascii=False, indent=2), "capability.task"),
            ActionSpec("task.claim", "Claim task", "认领一个未分配任务。", {"type": "object", "properties": {"task_id": {"type": "integer"}, "owner": {"type": "string"}}, "required": ["task_id", "owner"]}, lambda args: self.claim(args["task_id"], args["owner"]), "capability.task"),
        ]

    def create(self, subject: str, description: str, blocked_by: list[int]) -> str:
        payload = {"id": self._next_id(), "subject": subject, "description": description, "status": "pending", "owner": "", "blocked_by": blocked_by}
        self._save(payload)
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def update(self, task_id: int, status: str | None, owner: str | None, add_blocked_by: list[int], remove_blocked_by: list[int]) -> str:
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
            payload["blocked_by"] = [item for item in payload.get("blocked_by", []) if item not in remove_blocked_by]
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
        rows = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(self.tasks_dir.glob("task_*.json"))]
        return json.dumps(rows, ensure_ascii=False, indent=2)

    def unclaimed_tasks(self) -> list[dict]:
        rows = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(self.tasks_dir.glob("task_*.json"))]
        return [row for row in rows if row.get("status") == "pending" and not row.get("owner") and not row.get("blocked_by")]

    def state_fragments(self) -> list[str]:
        rows = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(self.tasks_dir.glob("task_*.json"))]
        if not rows:
            return ["tasks: (none)"]
        summary = "\n".join(f"- #{row['id']} {row['subject']} | {row['status']} | owner={row['owner'] or '-'} | blocked_by={row.get('blocked_by', [])}" for row in rows[:10])
        return [f"tasks:\n{summary}"]
