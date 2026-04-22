from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import RuntimePaths


def ensure_runtime_paths(base_dir: Path, user_id: str, conversation_id: str, task_id: str) -> RuntimePaths:
    root = base_dir / user_id / conversation_id / task_id
    history_dir = root / "history"
    state_dir = root / "state"
    workspace_dir = root / "workspaces"
    inbox_dir = root / "inbox"
    logs_dir = root / "logs"
    for path in (history_dir, state_dir, workspace_dir, inbox_dir, logs_dir):
        path.mkdir(parents=True, exist_ok=True)
    return RuntimePaths(root, history_dir, state_dir, workspace_dir, inbox_dir, logs_dir)


class JsonStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def read(self, default):
        if not self.path.exists():
            return default
        return json.loads(self.path.read_text(encoding="utf-8"))

    def write(self, payload) -> None:
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class JsonlStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, row: dict) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    def read_all(self) -> list[dict]:
        if not self.path.exists():
            return []
        rows = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
        return rows

    def replace(self, rows: Iterable[dict]) -> None:
        with self.path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
