from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wiki.service import SharedWikiService


ATTACHMENT_INGEST_STATE = "attachment_ingest.json"


@dataclass(slots=True)
class ServiceHub:
    knowledge_hub: Any
    attachment_ingestion: Any | None = None


class KnowledgeHubService:
    """Explicit service boundary for the canonical knowledge adapter."""

    service_name = "knowledge_hub"

    def __init__(self, *, project_root: Path, registry, session, hub_name: str = "default"):  # noqa: ANN001
        self.project_root = Path(project_root).resolve()
        self.registry = registry
        self.session = session
        self.hub_name = hub_name
        self.shared = SharedWikiService(project_root=self.project_root, registry=self.registry)

    @property
    def root(self) -> Path:
        return self.shared.store.root

    def ensure_bootstrap(self) -> None:
        self.shared.ensure_store()

    def refresh_from_registry(self) -> str:
        return self.shared.refresh_system()

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


class AttachmentIngestionService:
    """Owns the attachment-ingestion state contract."""

    def __init__(self, *, knowledge_hub, session):  # noqa: ANN001
        self.knowledge_hub = knowledge_hub
        self.session = session

    def ingest(self, files: list[dict[str, Any]] | None) -> str | None:
        if not files:
            return None
        result_text = self.knowledge_hub.ingest_user_files(files)
        payload = self._coerce_payload(result_text)
        snapshot = {
            "updated_at": self._utc_now(),
            "file_count": len(files),
            "file_names": [str(item.get("name") or "") for item in files],
            "result": payload,
        }
        self.session.write_state_json(ATTACHMENT_INGEST_STATE, snapshot)
        return result_text

    def latest_snapshot(self) -> dict[str, Any]:
        return self.session.read_state_json(ATTACHMENT_INGEST_STATE, {}) or {}

    def state_fragments(self) -> list[str]:
        snapshot = self.latest_snapshot()
        if not snapshot:
            return []
        names = ", ".join(name for name in snapshot.get("file_names", []) if name) or "(unnamed)"
        result = snapshot.get("result") or {}
        statuses: list[str] = []
        if isinstance(result, dict):
            for row in result.get("files", []) or []:
                name = str(row.get("name") or "(unnamed)")
                status = str(row.get("status") or "unknown")
                statuses.append(f"{name}:{status}")
        status_summary = ", ".join(statuses[:8]) if statuses else "no parsed status"
        return [
            (
                "Attachment ingestion state -> "
                f"updated_at={snapshot.get('updated_at', '')}; "
                f"file_count={snapshot.get('file_count', 0)}; "
                f"files={names}; "
                f"statuses={status_summary}"
            )
        ]

    def _coerce_payload(self, text: str) -> Any:
        try:
            return json.loads(text)
        except Exception:  # noqa: BLE001
            return {"status": "opaque", "raw_text": text}

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
