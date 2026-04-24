from __future__ import annotations

import json
import subprocess
import threading
import uuid

from schemas.action import ActionSpec

from .base import Capability


class BackgroundCapability(Capability):
    capability_name = "background"
    tasks_file = "background_tasks.json"
    notifications_file = "background_notifications.json"

    def bind(self, runtime) -> None:
        super().bind(runtime)
        self._lock = threading.Lock()
        if self.runtime.session.read_state_json(self.tasks_file, None) is None:
            self.runtime.session.write_state_json(self.tasks_file, {})

    def action_specs(self):
        return [
            ActionSpec(
                "background.run",
                "Run background command",
                "Run a shell command in the background without blocking the current chat.",
                {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
                lambda args: self.run(args["command"]),
                "capability.background",
            ),
            ActionSpec(
                "background.check",
                "Check background task",
                "Check the status of a background task.",
                {"type": "object", "properties": {"task_id": {"type": "string"}}, "required": ["task_id"]},
                lambda args: self.check(args["task_id"]),
                "capability.background",
            ),
        ]

    def _read_tasks(self) -> dict:
        return self.runtime.session.read_state_json(self.tasks_file, {})

    def _write_tasks(self, payload: dict) -> None:
        self.runtime.session.write_state_json(self.tasks_file, payload)

    def _read_notifications(self) -> list[dict]:
        return self.runtime.session.read_state_json(self.notifications_file, [])

    def _write_notifications(self, rows: list[dict]) -> None:
        self.runtime.session.write_state_json(self.notifications_file, rows)

    def run(self, command: str) -> str:
        task_id = str(uuid.uuid4())[:8]
        with self._lock:
            payload = self._read_tasks()
            payload[task_id] = {"status": "running", "command": command}
            self._write_tasks(payload)
        threading.Thread(target=self._execute, args=(task_id, command), daemon=True).start()
        self.runtime.events.emit("background.started", task_id=task_id)
        return f"Background task {task_id} started"

    def _execute(self, task_id: str, command: str) -> None:
        try:
            completed = subprocess.run(
                command,
                shell=True,
                cwd=self.runtime.session.workspace_root,
                capture_output=True,
                text=True,
                timeout=300,
            )
            status = "completed"
            output = (completed.stdout + completed.stderr).strip()[:50000]
        except Exception as exc:  # noqa: BLE001
            status = "failed"
            output = str(exc)

        with self._lock:
            payload = self._read_tasks()
            payload.setdefault(task_id, {"command": command})
            payload[task_id]["status"] = status
            payload[task_id]["output"] = output
            self._write_tasks(payload)
            notifications = self._read_notifications()
            notifications.append({"task_id": task_id, "status": status, "output": output[:1000]})
            self._write_notifications(notifications)
        self.runtime.events.emit(f"background.{status}", task_id=task_id, output=output[:1000])

    def check(self, task_id: str) -> str:
        payload = self._read_tasks().get(task_id) or {"error": f"Unknown task {task_id}"}
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def before_user_turn(self, message: str) -> None:
        with self._lock:
            rows = self._read_notifications()
            if not rows:
                return
            text = "\n".join(
                f"[bg:{row['task_id']}] {row['status']} -> {row['output'][:500]}"
                for row in rows
            )
            self.runtime.session.history.append_system(f"<background_notifications>\n{text}\n</background_notifications>")
            self._write_notifications([])

