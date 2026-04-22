from __future__ import annotations

import difflib
from pathlib import Path
from typing import Iterable

from agents.core.models import ActionSpec
from agents.toolboxes.base import Toolbox


class FileToolbox(Toolbox):
    toolbox_name = "files"

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None

    def spawn(self, workspace_root: Path) -> "FileToolbox":
        return FileToolbox(workspace_root=workspace_root)

    def _safe_path(self, raw: str) -> Path:
        if self.workspace_root is None:
            raise ValueError("FileToolbox workspace not bound yet.")
        path = (self.workspace_root / raw).resolve()
        if not path.is_relative_to(self.workspace_root):
            raise ValueError(f"Path escapes workspace: {raw}")
        return path

    def action_specs(self) -> Iterable[ActionSpec]:
        return [
            ActionSpec(
                "files.read_text",
                "Read text",
                "Read a text file from the workspace.",
                {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
                lambda args: self._safe_path(args["path"]).read_text(encoding="utf-8"),
                self.toolbox_name,
                "Useful for source files, docs, and config files.",
            ),
            ActionSpec(
                "files.write_text",
                "Write text",
                "Write a text file inside the workspace, creating parent directories when needed.",
                {
                    "type": "object",
                    "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                    "required": ["path", "content"],
                },
                lambda args: self._write(args["path"], args["content"]),
                self.toolbox_name,
                "Useful for reports, generated code, and scratch files.",
            ),
            ActionSpec(
                "files.edit_text",
                "Edit text",
                "Replace one exact text fragment inside an existing workspace file.",
                {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "old_text": {"type": "string"},
                        "new_text": {"type": "string"},
                    },
                    "required": ["path", "old_text", "new_text"],
                },
                lambda args: self._edit(args["path"], args["old_text"], args["new_text"]),
                self.toolbox_name,
                "Useful for targeted edits when the surrounding file should stay intact.",
            ),
            ActionSpec(
                "files.list_dir",
                "List dir",
                "List files and directories inside a workspace directory.",
                {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
                lambda args: self._list_dir(args["path"]),
                self.toolbox_name,
            ),
            ActionSpec(
                "files.diff_text",
                "Diff files",
                "Show a unified diff between two workspace text files.",
                {
                    "type": "object",
                    "properties": {"old_path": {"type": "string"}, "new_path": {"type": "string"}},
                    "required": ["old_path", "new_path"],
                },
                lambda args: self._diff(args["old_path"], args["new_path"]),
                self.toolbox_name,
            ),
        ]

    def _write(self, path: str, content: str) -> str:
        target = self._safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} chars to {path}"

    def _edit(self, path: str, old_text: str, new_text: str) -> str:
        target = self._safe_path(path)
        content = target.read_text(encoding="utf-8")
        if old_text not in content:
            raise ValueError(f"old_text not found in {path}")
        target.write_text(content.replace(old_text, new_text, 1), encoding="utf-8")
        return f"Edited {path}"

    def _list_dir(self, path: str) -> str:
        target = self._safe_path(path)
        if not target.exists():
            raise FileNotFoundError(path)
        return "\n".join(item.name + ("/" if item.is_dir() else "") for item in sorted(target.iterdir()))

    def _diff(self, old_path: str, new_path: str) -> str:
        old_lines = self._safe_path(old_path).read_text(encoding="utf-8").splitlines()
        new_lines = self._safe_path(new_path).read_text(encoding="utf-8").splitlines()
        return "\n".join(
            difflib.unified_diff(old_lines, new_lines, fromfile=old_path, tofile=new_path, lineterm="")
        )
