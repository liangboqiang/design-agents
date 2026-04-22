from __future__ import annotations

from pathlib import Path
from typing import Any

from wiki.service import SharedWikiService


class KnowledgeHubService:
    """Shared wiki-backed knowledge service.

    The wiki store lives under ``project_root/data/wiki`` and is not tied to a
    runtime session. Session state keeps only attachment ingest hints.
    """

    def __init__(self, *, project_root: Path, registry, session):  # noqa: ANN001
        self.project_root = Path(project_root).resolve()
        self.registry = registry
        self.session = session
        self.engine = None
        self.shared = SharedWikiService(project_root=self.project_root, registry=self.registry)

    def bind_engine(self, engine) -> None:  # noqa: ANN001
        self.engine = engine

    def ensure_bootstrap(self) -> str:
        self.shared.ensure_store()
        return "Wiki store initialized."

    def refresh_from_registry(self) -> str:
        if self.engine is None:
            raise RuntimeError("KnowledgeHubService is not bound to engine.")
        return self.shared.refresh_system(engine=self.engine)

    def ingest_user_files(self, files: list[dict[str, Any]] | None) -> str:
        return self.shared.ingest_user_files(files or [])

    def system_brief(self) -> str:
        return self.shared.system_brief()

    def search(self, query: str, limit: int = 20) -> str:
        return self.shared.search(query, limit=limit)

    def read_page(self, page_id: str) -> str:
        return self.shared.read_page(page_id)

    def read_source(self, page_id: str) -> str:
        return self.shared.read_source(page_id)

    def answer(self, query: str, limit: int = 5) -> str:
        return self.shared.answer(query, limit=limit)

    def lint(self) -> str:
        return self.shared.lint()


class AttachmentIngestionService:
    STATE_FILE = "attachment_ingress_snapshot.json"

    def __init__(self, *, knowledge_hub: KnowledgeHubService, session):  # noqa: ANN001
        self.knowledge_hub = knowledge_hub
        self.session = session

    def ingest(self, files: list[dict[str, Any]] | None) -> str:
        files = files or []
        names = [self._file_name(item, idx) for idx, item in enumerate(files, start=1)]
        snapshot = {
            "file_count": len(files),
            "file_names": names,
        }
        self.session.write_state_json(self.STATE_FILE, snapshot)
        if not files:
            return ""
        return self.knowledge_hub.ingest_user_files(files)

    def latest_snapshot(self) -> dict[str, Any]:
        return self.session.read_state_json(self.STATE_FILE, default={})

    def state_fragments(self) -> list[str]:
        snapshot = self.latest_snapshot()
        count = int(snapshot.get("file_count") or 0)
        if count <= 0:
            return []
        names = snapshot.get("file_names") or []
        joined = ", ".join(str(name) for name in names[:12])
        return [f"Attachment context: {count} file(s) currently ingested: {joined}"]

    @staticmethod
    def _file_name(item: dict[str, Any], idx: int) -> str:
        return str(
            item.get("name")
            or item.get("filename")
            or item.get("title")
            or item.get("path")
            or f"attachment_{idx}"
        )
