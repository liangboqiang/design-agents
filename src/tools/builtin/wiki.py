from __future__ import annotations

from pathlib import Path
from typing import Iterable

from schemas.action import ActionSpec
from tools.indexes.toolbox_registry import Toolbox


class WikiToolbox(Toolbox):
    toolbox_name = "wiki"
    tags = ("builtin", "wiki", "readonly")

    def spawn(self, workspace_root: Path) -> "WikiToolbox":
        return WikiToolbox(workspace_root=workspace_root)

    def action_specs(self) -> Iterable[ActionSpec]:
        return [
            ActionSpec(
                "wiki.search",
                "Search wiki",
                "Search shared wiki pages.",
                {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
                lambda args: self.engine.knowledge_hub.search(str(args["query"])),
                self.toolbox_name,
            ),
            ActionSpec(
                "wiki.read_page",
                "Read wiki page",
                "Read one wiki page markdown.",
                {"type": "object", "properties": {"page_id": {"type": "string"}}, "required": ["page_id"]},
                lambda args: self.engine.knowledge_hub.read_page(str(args["page_id"])),
                self.toolbox_name,
            ),
            ActionSpec(
                "wiki.read_source",
                "Read source",
                "Read the original source text linked from a wiki page.",
                {"type": "object", "properties": {"page_id": {"type": "string"}}, "required": ["page_id"]},
                lambda args: self.engine.knowledge_hub.read_source(str(args["page_id"])),
                self.toolbox_name,
            ),
            ActionSpec(
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
                lambda args: self.engine.knowledge_hub.answer(str(args["query"]), int(args.get("limit") or 5)),
                self.toolbox_name,
            ),
        ]


class WikiAdminToolbox(Toolbox):
    toolbox_name = "wiki_admin"
    tags = ("builtin", "wiki", "admin")

    def spawn(self, workspace_root: Path) -> "WikiAdminToolbox":
        return WikiAdminToolbox(workspace_root=workspace_root)

    def action_specs(self) -> Iterable[ActionSpec]:
        return [
            ActionSpec(
                "wiki_admin.refresh_system",
                "Refresh wiki system pages",
                "Scan allowed system/business sources and rebuild shared wiki pages through subagent batch extraction.",
                {"type": "object", "properties": {}},
                lambda args: self.engine.refresh_wiki(),
                self.toolbox_name,
            ),
            ActionSpec(
                "wiki_admin.ingest_files",
                "Ingest files into wiki",
                "Record user files into shared wiki.",
                {"type": "object", "properties": {"files": {"type": "array"}}, "required": ["files"]},
                lambda args: self.engine.ingest_files(list(args.get("files") or [])),
                self.toolbox_name,
            ),
            ActionSpec(
                "wiki_admin.lint",
                "Lint wiki",
                "Check catalog/page consistency.",
                {"type": "object", "properties": {}},
                lambda args: self.engine.knowledge_hub.lint(),
                self.toolbox_name,
            ),
        ]
