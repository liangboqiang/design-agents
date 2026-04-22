from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class KnowledgeHubService:
    """Minimal runtime knowledge service.

    This version intentionally keeps runtime knowledge handling small and explicit:
    it stores lightweight attachment/ingest metadata in session state and exposes
    only the methods the engine and harness actually use.
    """

    STATE_FILE = "knowledge_hub_snapshot.json"

    def __init__(self, *, project_root: Path, registry, session):  # noqa: ANN001
        self.project_root = Path(project_root).resolve()
        self.registry = registry
        self.session = session

    def ensure_bootstrap(self) -> str:
        snapshot = self.session.read_state_json(self.STATE_FILE, default={})
        if snapshot:
            return "Knowledge hub already initialized."
        payload = {
            "skills_root": str(getattr(self.registry, "skills_root", self.project_root / "src/skills")),
            "attachment_count": 0,
            "attachment_names": [],
        }
        self.session.write_state_json(self.STATE_FILE, payload)
        return "Knowledge hub initialized."

    def refresh_from_registry(self) -> str:
        snapshot = self.session.read_state_json(self.STATE_FILE, default={})
        snapshot["skills_root"] = str(getattr(self.registry, "skills_root", self.project_root / "src/skills"))
        snapshot["refreshed"] = True
        self.session.write_state_json(self.STATE_FILE, snapshot)
        return "Knowledge hub refreshed from registry."

    def ingest_user_files(self, files: list[dict[str, Any]] | None) -> str:
        files = files or []
        names = [self._file_name(item, idx) for idx, item in enumerate(files, start=1)]
        snapshot = self.session.read_state_json(self.STATE_FILE, default={})
        snapshot["attachment_count"] = len(files)
        snapshot["attachment_names"] = names
        snapshot["attachments"] = [self._file_summary(item, idx) for idx, item in enumerate(files, start=1)]
        self.session.write_state_json(self.STATE_FILE, snapshot)
        if not names:
            return "No files ingested."
        return json.dumps({"ingested": len(names), "files": names}, ensure_ascii=False, indent=2)

    def system_brief(self) -> str:
        snapshot = self.session.read_state_json(self.STATE_FILE, default={})
        names = snapshot.get("attachment_names") or []
        if not names:
            return "Knowledge hub: no ingested user files in current task context."
        joined = ", ".join(str(name) for name in names[:12])
        return f"Knowledge hub: current task has {len(names)} ingested file(s): {joined}"

    @staticmethod
    def _file_name(item: dict[str, Any], idx: int) -> str:
        return str(
            item.get("name")
            or item.get("filename")
            or item.get("title")
            or item.get("path")
            or f"attachment_{idx}"
        )

    def _file_summary(self, item: dict[str, Any], idx: int) -> dict[str, Any]:
        return {
            "name": self._file_name(item, idx),
            "mime_type": item.get("mime_type") or item.get("content_type") or "",
            "path": str(item.get("path") or item.get("local_path") or ""),
            "size": item.get("size"),
        }


class AttachmentIngestionService:
    STATE_FILE = "attachment_ingress_snapshot.json"

    def __init__(self, *, knowledge_hub: KnowledgeHubService, session):  # noqa: ANN001
        self.knowledge_hub = knowledge_hub
        self.session = session

    def ingest(self, files: list[dict[str, Any]] | None) -> str:
        files = files or []
        names = [KnowledgeHubService._file_name(item, idx) for idx, item in enumerate(files, start=1)]
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
