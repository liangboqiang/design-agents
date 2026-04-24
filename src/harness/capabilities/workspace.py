from __future__ import annotations

import json
import subprocess

from schemas.action import ActionSpec

from .base import Capability


class WorkspaceCapability(Capability):
    capability_name = "workspace"

    def action_specs(self):
        return [
            ActionSpec(
                "workspace.create",
                "Create workspace",
                "Create an isolated workspace.",
                {"type": "object", "properties": {"name": {"type": "string"}, "task_id": {"type": "integer"}}, "required": ["name"]},
                lambda args: self.create(args["name"], args.get("task_id")),
                "capability.workspace",
            ),
            ActionSpec(
                "workspace.list",
                "List workspaces",
                "List current workspaces.",
                {"type": "object", "properties": {}},
                lambda args: json.dumps({"workspaces": self.engine.session.workspaces.list_all()}, ensure_ascii=False, indent=2),
                "capability.workspace",
            ),
            ActionSpec(
                "workspace.run",
                "Run command in workspace",
                "Run a shell command inside a named workspace.",
                {"type": "object", "properties": {"name": {"type": "string"}, "command": {"type": "string"}}, "required": ["name", "command"]},
                lambda args: self.run(args["name"], args["command"]),
                "capability.workspace",
            ),
            ActionSpec(
                "workspace.keep",
                "Keep workspace",
                "Mark a workspace as kept.",
                {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
                lambda args: self.keep(args["name"]),
                "capability.workspace",
            ),
            ActionSpec(
                "workspace.remove",
                "Remove workspace",
                "Remove a workspace and optionally complete its task.",
                {
                    "type": "object",
                    "properties": {"name": {"type": "string"}, "complete_task": {"type": "boolean"}},
                    "required": ["name"],
                },
                lambda args: self.remove(args["name"], bool(args.get("complete_task", False))),
                "capability.workspace",
            ),
        ]

    def create(self, name: str, task_id: int | None) -> str:
        row = self.engine.session.workspaces.create(name, task_id)
        task_cap = self.capability("task")
        if task_id and task_cap:
            task_cap.update(
                task_id,
                status="in_progress",
                owner=self.engine.engine_id,
                add_blocked_by=[],
                remove_blocked_by=[],
            )
        self.engine.events.emit("workspace.created", workspace=row)
        return json.dumps(row, ensure_ascii=False, indent=2)

    def run(self, name: str, command: str) -> str:
        row = self.engine.session.workspaces.get(name)
        completed = subprocess.run(command, shell=True, cwd=row["path"], capture_output=True, text=True, timeout=300)
        output = (completed.stdout + completed.stderr).strip()
        self.engine.events.emit("workspace.command_ran", workspace=name, command=command)
        return output[:50000] if output else "(no output)"

    def keep(self, name: str) -> str:
        row = self.engine.session.workspaces.keep(name)
        self.engine.events.emit("workspace.kept", workspace=row)
        return f"Workspace {name} kept"

    def remove(self, name: str, complete_task: bool) -> str:
        row = self.engine.session.workspaces.remove(name)
        task_cap = self.capability("task")
        if complete_task and row.get("task_id") and task_cap:
            task_cap.update(
                int(row["task_id"]),
                status="completed",
                owner=self.engine.engine_id,
                add_blocked_by=[],
                remove_blocked_by=[],
            )
        self.engine.events.emit("workspace.removed", workspace=row, complete_task=complete_task)
        return f"Workspace {name} removed"

