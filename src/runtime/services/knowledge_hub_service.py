from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.wiki_hub import WikiHub


class KnowledgeHubService:
    """Explicit service boundary for the canonical knowledge hub.

    The runtime can depend on this service without letting orchestration code
    know any WikiHub implementation details.
    """

    service_name = "knowledge_hub"

    def __init__(self, *, project_root: Path, registry, session, hub_name: str = "default"):  # noqa: ANN001
        self._hub = WikiHub(project_root=project_root, registry=registry, session=session, hub_name=hub_name)

    @property
    def root(self) -> Path:
        return self._hub.root

    def ensure_bootstrap(self) -> None:
        self._hub.ensure_bootstrap()

    def refresh_from_registry(self) -> str:
        return self._hub.refresh_from_registry()

    def ingest_user_files(self, files: list[dict[str, Any]] | None) -> str:
        return self._hub.ingest_user_files(files)

    def search(self, query: str, limit: int = 10, groups: list[str] | None = None) -> str:
        return self._hub.search(query=query, limit=limit, groups=groups)

    def read_page(self, page: str) -> str:
        return self._hub.read_page(page)

    def answer(self, query: str, limit: int = 5) -> str:
        return self._hub.answer(query=query, limit=limit)

    def lint(self) -> str:
        return self._hub.lint()

    def system_brief(self) -> str:
        return self._hub.system_brief()
