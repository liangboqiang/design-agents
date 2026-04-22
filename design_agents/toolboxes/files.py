from __future__ import annotations

import difflib
from pathlib import Path
from typing import Iterable

from design_agents.core.models import ActionSpec
from design_agents.toolboxes.base import Toolbox


class FileToolbox(Toolbox):
    toolbox_name = "files"

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None

    def bind_workspace(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.resolve()

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
                "读取工作区内文本文件内容。",
                {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
                lambda args: self._safe_path(args["path"]).read_text(encoding="utf-8"),
                self.toolbox_name,
                "适合读取代码、说明文档、配置文件。",
            ),
            ActionSpec(
                "files.write_text",
                "Write text",
                "写入文本文件；如果目录不存在则自动创建。",
                {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]},
                lambda args: self._write(args["path"], args["content"]),
                self.toolbox_name,
                "适合生成报告、代码、草稿、缓存摘要。",
            ),
            ActionSpec(
                "files.edit_text",
                "Edit text",
                "在已有文件中进行一次精确替换。",
                {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["path", "old_text", "new_text"]},
                lambda args: self._edit(args["path"], args["old_text"], args["new_text"]),
                self.toolbox_name,
                "适合对单处文本进行精确修改。",
            ),
            ActionSpec(
                "files.list_dir",
                "List dir",
                "列出目录下的文件和子目录。",
                {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
                lambda args: self._list_dir(args["path"]),
                self.toolbox_name,
            ),
            ActionSpec(
                "files.diff_text",
                "Diff files",
                "对比两个文本文件差异。",
                {"type": "object", "properties": {"old_path": {"type": "string"}, "new_path": {"type": "string"}}, "required": ["old_path", "new_path"]},
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
        return "\n".join(difflib.unified_diff(old_lines, new_lines, fromfile=old_path, tofile=new_path, lineterm=""))
