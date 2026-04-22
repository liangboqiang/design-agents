from __future__ import annotations

from pathlib import Path
from typing import Iterable

from schemas.action import ActionSpec
from tools.indexes.toolbox_registry import Toolbox


class WikiToolbox(Toolbox):
    toolbox_name = "wiki"
    tags = ("builtin", "knowledge", "wiki")

    def spawn(self, workspace_root: Path) -> "WikiToolbox":
        return WikiToolbox(workspace_root=workspace_root)

    def _hub(self):
        if self.engine is None:
            raise ValueError("WikiToolbox engine not bound yet.")
        return getattr(self.engine, "knowledge_hub", None) or getattr(self.engine, "wiki_hub")

    def action_specs(self) -> Iterable[ActionSpec]:
        return [
            ActionSpec(
                "wiki.refresh",
                "Refresh wiki",
                "Scan business docs, system self-description, and user-ingested sources into the LLM Wiki hub.",
                {"type": "object", "properties": {}},
                lambda args: self._hub().refresh_from_registry(),
                self.toolbox_name,
                "Use when the repo or knowledge sources changed.",
                tags=("wiki", "refresh"),
            ),
            ActionSpec(
                "wiki.ingest_files",
                "Ingest files",
                "Ingest user-provided attachments into the wiki hub. files must follow the standard array with name/url.",
                {
                    "type": "object",
                    "properties": {
                        "files": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "url": {"type": "string"},
                                },
                                "required": ["name", "url"],
                            },
                        }
                    },
                    "required": ["files"],
                },
                lambda args: self._hub().ingest_user_files(args["files"]),
                self.toolbox_name,
                tags=("wiki", "ingest", "attachment"),
            ),
            ActionSpec(
                "wiki.search",
                "Search wiki",
                "Search compiled wiki pages only. This is the preferred knowledge lookup entrypoint.",
                {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                    "required": ["query"],
                },
                lambda args: self._hub().search(args["query"], limit=int(args.get("limit", 10))),
                self.toolbox_name,
                tags=("wiki", "search"),
            ),
            ActionSpec(
                "wiki.read_page",
                "Read wiki page",
                "Read one compiled wiki page by relative path, stem, or title.",
                {"type": "object", "properties": {"page": {"type": "string"}}, "required": ["page"]},
                lambda args: self._hub().read_page(args["page"]),
                self.toolbox_name,
                tags=("wiki", "read"),
            ),
            ActionSpec(
                "wiki.answer",
                "Answer from wiki",
                "Return a compact knowledge context synthesized strictly from wiki pages.",
                {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                    "required": ["query"],
                },
                lambda args: self._hub().answer(args["query"], limit=int(args.get("limit", 5))),
                self.toolbox_name,
                tags=("wiki", "answer"),
            ),
            ActionSpec(
                "wiki.lint",
                "Lint wiki",
                "Check wiki health including broken wiki-links and orphan pages.",
                {"type": "object", "properties": {}},
                lambda args: self._hub().lint(),
                self.toolbox_name,
                tags=("wiki", "lint"),
            ),
        ]
