from __future__ import annotations

import json
import shutil
import subprocess
import time

from design_agents.capabilities.base import Capability
from design_agents.core.models import ActionSpec
from design_agents.core.storage import JsonStore, JsonlStore


class WorkspaceCapability(Capability):
    capability_name = "workspace"

    def bind(self, engine) -> None:
        super().bind(engine)
        self.index = JsonStore(engine.paths.workspace_dir / "index.json")
        self.events = JsonlStore(engine.paths.workspace_dir / "events.jsonl")
        if not self.index.path.exists():
            self.index.write({"workspaces": []})

    def action_specs(self):
        return [
            ActionSpec("workspace.create", "Create workspace", "创建独立工作空间。", {"type": "object", "properties": {"name": {"type": "string"}, "task_id": {"type": "integer"}}, "required": ["name"]}, lambda args: self.create(args["name"], args.get("task_id")), "capability.workspace"),
            ActionSpec("workspace.list", "List workspaces", "列出工作空间索引。", {"type": "object", "properties": {}}, lambda args: json.dumps(self.index.read({"workspaces": []}), ensure_ascii=False, indent=2), "capability.workspace"),
            ActionSpec("workspace.run", "Run command in workspace", "在某个工作空间中执行 shell 命令。", {"type": "object", "properties": {"name": {"type": "string"}, "command": {"type": "string"}}, "required": ["name", "command"]}, lambda args: self.run(args["name"], args["command"]), "capability.workspace"),
            ActionSpec("workspace.keep", "Keep workspace", "标记工作空间为保留状态。", {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}, lambda args: self.keep(args["name"]), "capability.workspace"),
            ActionSpec("workspace.remove", "Remove workspace", "移除工作空间，可选同时完成绑定任务。", {"type": "object", "properties": {"name": {"type": "string"}, "complete_task": {"type": "boolean"}}, "required": ["name"]}, lambda args: self.remove(args["name"], bool(args.get("complete_task", False))), "capability.workspace"),
        ]

    def _rows(self):
        return list(self.index.read({"workspaces": []})["workspaces"])

    def _save(self, rows):
        self.index.write({"workspaces": rows})

    def _find(self, name: str):
        for row in self._rows():
            if row["name"] == name:
                return row
        raise ValueError(f"Unknown workspace {name}")

    def create(self, name: str, task_id: int | None) -> str:
        path = self.engine.paths.workspace_dir / name
        if path.exists():
            raise ValueError(f"Workspace already exists: {name}")
        path.mkdir(parents=True)
        row = {"name": name, "path": str(path), "task_id": task_id, "status": "active"}
        rows = self._rows(); rows.append(row); self._save(rows)
        self.events.append({"ts": time.time(), "event": "workspace.create", "workspace": row})
        if task_id and self.engine.capability("task"):
            self.engine.capability("task").update(task_id, status="in_progress", owner=self.engine.engine_id, add_blocked_by=[], remove_blocked_by=[])
        return json.dumps(row, ensure_ascii=False, indent=2)

    def run(self, name: str, command: str) -> str:
        row = self._find(name)
        completed = subprocess.run(command, shell=True, cwd=row["path"], capture_output=True, text=True, timeout=300)
        output = (completed.stdout + completed.stderr).strip()
        return output[:50000] if output else "(no output)"

    def keep(self, name: str) -> str:
        rows = self._rows()
        for row in rows:
            if row["name"] == name:
                row["status"] = "kept"
        self._save(rows)
        self.events.append({"ts": time.time(), "event": "workspace.keep", "name": name})
        return f"Workspace {name} kept"

    def remove(self, name: str, complete_task: bool) -> str:
        rows = self._rows(); target = None; kept = []
        for row in rows:
            if row["name"] == name: target = row
            else: kept.append(row)
        if target is None:
            raise ValueError(f"Unknown workspace {name}")
        shutil.rmtree(target["path"], ignore_errors=True)
        self._save(kept)
        if complete_task and target.get("task_id") and self.engine.capability("task"):
            self.engine.capability("task").update(int(target["task_id"]), status="completed", owner=self.engine.engine_id, add_blocked_by=[], remove_blocked_by=[])
        self.events.append({"ts": time.time(), "event": "workspace.remove", "workspace": target, "complete_task": complete_task})
        return f"Workspace {name} removed"
