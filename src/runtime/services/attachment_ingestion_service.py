from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


ATTACHMENT_INGEST_STATE = "attachment_ingest.json"


class AttachmentIngestionService:
    """Owns the attachment-ingestion state contract.

    Harness should not know how attachments become knowledge. This service owns
    the only formal state artifact for that flow.
    """

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
