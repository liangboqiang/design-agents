from __future__ import annotations

from pathlib import Path
from typing import Any

from wiki.service import SharedWikiService


class KnowledgeHubService:
    """Explicit service boundary for the canonical knowledge adapter."""

    service_name = "knowledge_hub"

    def __init__(self, *, project_root: Path, registry, session, hub_name: str = "default"):  # noqa: ANN001
        self.project_root = Path(project_root).resolve()
        self.registry = registry
        self.session = session
        self.hub_name = hub_name
        self.engine = None
        self.shared = SharedWikiService(project_root=self.project_root, registry=self.registry)

    def bind_engine(self, engine) -> None:  # noqa: ANN001
        self.engine = engine

    @property
    def root(self) -> Path:
        return self.shared.store.root

    def ensure_bootstrap(self) -> None:
        self.shared.ensure_store()

    def refresh_from_registry(self) -> str:
        return self.shared.refresh_system(engine=self.engine)

    def ingest_user_files(self, files: list[dict[str, Any]] | None) -> str:
        return self.shared.ingest_user_files(files or [])

    def search(self, query: str, limit: int = 10, groups: list[str] | None = None) -> str:
        return self.shared.search(query=query, limit=limit)

    def read_page(self, page: str) -> str:
        return self.shared.read_page(page)

    def read_source(self, page: str) -> str:
        return self.shared.read_source(page)

    def answer(self, query: str, limit: int = 5) -> str:
        return self.shared.answer(query=query, limit=limit)

    def lint(self) -> str:
        return self.shared.lint()

    def system_brief(self) -> str:
        return self.shared.system_brief()
