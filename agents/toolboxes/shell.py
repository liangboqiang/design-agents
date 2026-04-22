from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable

from agents.core.models import ActionSpec
from agents.toolboxes.base import Toolbox


class ShellToolbox(Toolbox):
    toolbox_name = "shell"

    def __init__(self, workspace_root: Path | None = None, timeout: int = 120):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.timeout = timeout

    def clone(self) -> "ShellToolbox":
        return ShellToolbox(timeout=self.timeout)

    def bind_workspace(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.resolve()

    def action_specs(self) -> Iterable[ActionSpec]:
        return [
            ActionSpec(
                "shell.run",
                "Run shell command",
                "在当前工作区执行 shell 命令。",
                {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
                lambda args: self._run(args["command"]),
                self.toolbox_name,
                "适合运行测试、目录检查、脚本调用。",
            ),
        ]

    def _run(self, command: str) -> str:
        if self.workspace_root is None:
            raise ValueError("ShellToolbox workspace not bound yet.")
        blocked = ["rm -rf /", "shutdown", "reboot", "sudo "]
        if any(token in command for token in blocked):
            raise ValueError("Blocked dangerous shell command.")
        completed = subprocess.run(command, shell=True, cwd=self.workspace_root, capture_output=True, text=True, timeout=self.timeout)
        output = (completed.stdout + completed.stderr).strip()
        return output[:50000] if output else "(no output)"
