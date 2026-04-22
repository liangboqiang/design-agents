from __future__ import annotations

import json
import subprocess
import threading
import uuid

from agents.capabilities.base import Capability
from agents.core.models import ActionSpec
from agents.core.storage import JsonStore, JsonlStore


class BackgroundCapability(Capability):
    capability_name = "background"

    def bind(self, engine) -> None:
        super().bind(engine)
        self.task_store = JsonStore(engine.paths.state_dir / "background_tasks.json")
        self.notifs = JsonlStore(engine.paths.logs_dir / "background_notifications.jsonl")
        if not self.task_store.path.exists():
            self.task_store.write({})

    def action_specs(self):
        return [
            ActionSpec("background.run", "Run background command", "在后台运行 shell 命令，不阻塞当前对话。", {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}, lambda args: self.run(args["command"]), "capability.background"),
            ActionSpec("background.check", "Check background task", "查看后台任务状态。", {"type": "object", "properties": {"task_id": {"type": "string"}}, "required": ["task_id"]}, lambda args: self.check(args["task_id"]), "capability.background"),
        ]

    def run(self, command: str) -> str:
        task_id = str(uuid.uuid4())[:8]
        payload = self.task_store.read({})
        payload[task_id] = {"status": "running", "command": command}
        self.task_store.write(payload)
        threading.Thread(target=self._execute, args=(task_id, command), daemon=True).start()
        return f"Background task {task_id} started"

    def _execute(self, task_id: str, command: str) -> None:
        payload = self.task_store.read({})
        try:
            completed = subprocess.run(command, shell=True, cwd=self.engine.workspace_root, capture_output=True, text=True, timeout=300)
            output = (completed.stdout + completed.stderr).strip()[:50000]
            payload[task_id]["status"] = "completed"
            payload[task_id]["output"] = output
        except Exception as exc:
            payload[task_id]["status"] = "failed"
            payload[task_id]["output"] = str(exc)
        self.task_store.write(payload)
        self.notifs.append({"task_id": task_id, "status": payload[task_id]["status"], "output": payload[task_id]["output"][:1000]})

    def check(self, task_id: str) -> str:
        return json.dumps(self.task_store.read({}).get(task_id) or {"error": f"Unknown task {task_id}"}, ensure_ascii=False, indent=2)

    def before_user_turn(self, message: str) -> None:
        rows = self.notifs.read_all()
        if rows:
            text = "\n".join(f"[bg:{row['task_id']}] {row['status']} -> {row['output'][:500]}" for row in rows)
            self.engine.history.append_system(f"<background_notifications>\n{text}\n</background_notifications>")
            self.notifs.replace([])
