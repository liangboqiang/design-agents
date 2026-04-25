from __future__ import annotations

from pathlib import Path
from typing import Iterable

from protocol.types import ToolSpec


class WikiAdminToolbox:
    toolbox_name = "wiki_admin"
    tags = ("builtin", "wiki", "admin")

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime

    def spawn(self, workspace_root: Path) -> "WikiAdminToolbox":
        return WikiAdminToolbox(workspace_root=workspace_root)

    def tool_specs(self) -> Iterable[ToolSpec]:
        return [
            ToolSpec(
                "wiki_admin.refresh_system",
                "Refresh wiki system pages",
                "Scan allowed system/business sources and rebuild shared wiki pages through agent_build batch extraction.",
                {"type": "object", "properties": {}},
                lambda args: self.runtime.knowledge_hub.refresh_from_registry(),
                self.toolbox_name,
            ),
            ToolSpec(
                "wiki_admin.ingest_files",
                "Ingest files into wiki",
                "Record user files into the shared wiki store.",
                {"type": "object", "properties": {"files": {"type": "array"}}, "required": ["files"]},
                lambda args: self.runtime.knowledge_hub.ingest_user_files(list(args.get("files") or [])),
                self.toolbox_name,
            ),
        ]
