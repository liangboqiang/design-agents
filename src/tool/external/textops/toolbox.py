from __future__ import annotations

import difflib
from pathlib import Path
from typing import Iterable

from protocol.types import ToolSpec


class TextOpsToolbox:
    toolbox_name = "textops"
    tags = ("text",)

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime

    def spawn(self, workspace_root: Path) -> "TextOpsToolbox":
        return TextOpsToolbox(workspace_root=workspace_root)

    def tool_specs(self) -> Iterable[ToolSpec]:
        return [
            ToolSpec(
                "textops.search",
                "Search text",
                "Return line matches for a substring inside a workspace file.",
                {
                    "type": "object",
                    "properties": {"path": {"type": "string"}, "query": {"type": "string"}},
                    "required": ["path", "query"],
                },
                lambda args: self._search(args["path"], args["query"]),
                self.toolbox_name,
                tags=("text", "search"),
            ),
            ToolSpec(
                "textops.preview_replace",
                "Preview replace",
                "Show a unified diff for a one-shot text replacement without writing the file.",
                {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "old_text": {"type": "string"},
                        "new_text": {"type": "string"},
                    },
                    "required": ["path", "old_text", "new_text"],
                },
                lambda args: self._preview_replace(args["path"], args["old_text"], args["new_text"]),
                self.toolbox_name,
                tags=("text", "diff"),
            ),
        ]

    def _safe_path(self, raw: str) -> Path:
        if self.workspace_root is None:
            raise ValueError("TextOpsToolbox workspace not bound yet.")
        path = (self.workspace_root / raw).resolve()
        if not path.is_relative_to(self.workspace_root):
            raise ValueError(f"Path escapes workspace: {raw}")
        return path

    def _search(self, path: str, query: str) -> str:
        lines = self._safe_path(path).read_text(encoding="utf-8").splitlines()
        matches = [f"{index}: {line}" for index, line in enumerate(lines, start=1) if query in line]
        return "\n".join(matches) or "(no matches)"

    def _preview_replace(self, path: str, old_text: str, new_text: str) -> str:
        target = self._safe_path(path)
        before = target.read_text(encoding="utf-8")
        after = before.replace(old_text, new_text, 1)
        return "\n".join(
            difflib.unified_diff(
                before.splitlines(),
                after.splitlines(),
                fromfile=path,
                tofile=f"{path} (preview)",
                lineterm="",
            )
        )
