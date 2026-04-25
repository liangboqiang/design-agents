from __future__ import annotations

from pathlib import Path
from typing import Iterable

from protocol.types import ToolSpec


class WikiToolbox:
    toolbox_name = "wiki"
    tags = ("builtin", "wiki", "readonly")

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime

    def spawn(self, workspace_root: Path) -> "WikiToolbox":
        return WikiToolbox(workspace_root=workspace_root)

    def tool_specs(self) -> Iterable[ToolSpec]:
        return [
            ToolSpec(
                "wiki.search",
                "Search wiki",
                "Search shared wiki pages.",
                {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                    "required": ["query"],
                },
                lambda args: self.runtime.knowledge_hub.search(
                    str(args["query"]),
                    limit=int(args.get("limit") or 20),
                ),
                self.toolbox_name,
            ),
            ToolSpec(
                "wiki.read_page",
                "Read wiki page",
                "Read one wiki page markdown.",
                {"type": "object", "properties": {"page_id": {"type": "string"}}, "required": ["page_id"]},
                lambda args: self.runtime.knowledge_hub.read_page(str(args["page_id"])),
                self.toolbox_name,
            ),
            ToolSpec(
                "wiki.read_source",
                "Read source",
                "Read the original source text linked from a wiki page.",
                {"type": "object", "properties": {"page_id": {"type": "string"}}, "required": ["page_id"]},
                lambda args: self.runtime.knowledge_hub.read_source(str(args["page_id"])),
                self.toolbox_name,
            ),
            ToolSpec(
                "wiki.answer",
                "Answer from wiki",
                "Draft an answer from top wiki pages.",
                {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                    "required": ["query"],
                },
                lambda args: self.runtime.knowledge_hub.answer(
                    str(args["query"]),
                    limit=int(args.get("limit") or 5),
                ),
                self.toolbox_name,
            ),
        ]
