from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable

from schemas.action import ActionSpec
from tool.indexes.toolbox_registry import Toolbox


class ShellToolbox(Toolbox):
    toolbox_name = "shell"
    tags = ("builtin", "workspace", "exec")

    def __init__(self, workspace_root: Path | None = None, timeout: int = 120):
        super().__init__(workspace_root=workspace_root)
        self.timeout = timeout

    def spawn(self, workspace_root: Path) -> "ShellToolbox":
        return ShellToolbox(workspace_root=workspace_root, timeout=self.timeout)

    def action_specs(self) -> Iterable[ActionSpec]:
        return [
            ActionSpec(
                "shell.run",
                "Run shell command",
                "Run a shell command inside the current workspace.",
                {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
                lambda args: self._run(args["command"]),
                self.toolbox_name,
                "Useful for tests, inspections, and project scripts.",
                tags=("shell", "exec"),
            ),
        ]

    def _run(self, command: str) -> str:
        if self.workspace_root is None:
            raise ValueError("ShellToolbox workspace not bound yet.")
        blocked = ["rm -rf /", "shutdown", "reboot", "sudo "]
        if any(token in command for token in blocked):
            raise ValueError("Blocked dangerous shell command.")
        completed = subprocess.run(
            command,
            shell=True,
            cwd=self.workspace_root,
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )
        output = (completed.stdout + completed.stderr).strip()
        return output[:50000] if output else "(no output)"
