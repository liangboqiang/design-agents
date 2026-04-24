from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

from governance.repo_lint import lint_repository

from ..index import WikiIndexWriter
from ..render import WikiLinkRenderer
from ..search import WikiSearcher
from ..store import WikiStore


class SharedWikiService:
    """Shared knowledge adapter backed by ``src/wiki/store``."""

    def __init__(self, *, project_root: Path, registry):  # noqa: ANN001
        self.project_root = Path(project_root).resolve()
        self.registry = registry
        self.store = WikiStore(self.project_root)

    def ensure_store(self) -> None:
        self.store.ensure()

    def refresh_system(self, *, engine) -> str:  # noqa: ANN001
        self.ensure_store()
        refresh = getattr(self.registry, "refresh", None)
        if refresh is not None:
            refresh()
        result = getattr(self.registry, "protocol", None)
        if result is None:
            raise ValueError("Registry does not expose a protocol read model.")
        index_payload = WikiIndexWriter(self.store).write(result)
        job_id = f"refresh_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        self.store.write_job(
            job_id,
            {
                "job_id": job_id,
                "kind": "refresh_system",
                "entity_count": len(result.entities),
                "page_count": len(result.pages),
            },
        )

        index_payload["status"] = "ok"
        return json.dumps(index_payload, ensure_ascii=False, indent=2)

    def ingest_user_files(self, files: list[dict]) -> str:
        self.ensure_store()
        created: list[dict[str, str]] = []
        for index, item in enumerate(files or [], start=1):
            name = str(item.get("name") or item.get("filename") or item.get("path") or f"user_file_{index}")
            uri = str(item.get("url") or item.get("path") or "")
            status, stored_path = self._store_attachment(name=name, uri=uri)
            created.append({"name": name, "status": status, "stored_path": stored_path})
        return json.dumps({"status": "ok", "files": created}, ensure_ascii=False, indent=2)

    def search(self, query: str, limit: int = 20) -> str:
        searcher = WikiSearcher(store=self.store, read_text=self._read_repo_text)
        return json.dumps(searcher.search(query, limit=limit), ensure_ascii=False, indent=2)

    def read_page(self, page_id: str) -> str:
        self.ensure_store()
        catalog = self.store.read_catalog()
        row = (catalog.get("pages") or {}).get(page_id)
        if row is None:
            return f"Page not found: {page_id}"
        text = self._read_repo_text(str(row.get("path") or ""))
        renderer = WikiLinkRenderer(index=self.store.read_index(), catalog=catalog)
        return renderer.render(text)

    def read_source(self, page_id: str) -> str:
        self.ensure_store()
        index = self.store.read_index().get("entities") or {}
        row = index.get(page_id)
        if row is None:
            return self.read_page(page_id)
        folder = self.project_root / str(row.get("folder") or "")
        truth_ext = list(row.get("truth_ext") or [])
        if truth_ext:
            target = folder / truth_ext[0]
            if target.exists():
                return target.read_text(encoding="utf-8")
        return self.read_page(page_id)

    def answer(self, query: str, limit: int = 5) -> str:
        rows = json.loads(self.search(query, limit=limit))
        if not rows:
            return f"No wiki pages matched query: {query}"
        body = [f"# Wiki answer for: {query}", ""]
        for row in rows:
            body.append(f"## {row.get('title')}")
            body.append(str(row.get("summary") or ""))
            for point in (row.get("key_points") or [])[:5]:
                body.append(f"- {point}")
            body.append(f"- Source: {row.get('source_path') or row.get('source_uri')}")
            body.append("")
        return "\n".join(body).strip()

    def lint(self) -> str:
        return lint_repository(self.project_root)

    def system_brief(self) -> str:
        self.ensure_store()
        catalog = self.store.read_catalog()
        return f"Shared wiki store: {len(catalog.get('pages') or {})} page(s) available under src/wiki/store."

    def _read_repo_text(self, rel_path: str) -> str:
        path = (self.project_root / rel_path).resolve()
        if not path.exists():
            return f"Missing path: {rel_path}"
        return path.read_text(encoding="utf-8")

    def _store_attachment(self, *, name: str, uri: str) -> tuple[str, str]:
        target = self.store.attachments_dir / name
        parsed = urlparse(uri)
        try:
            if parsed.scheme in {"http", "https"}:
                response = requests.get(uri, timeout=20)
                response.raise_for_status()
                target.write_bytes(response.content)
                return "stored", str(target)
            source = Path(uri.replace("file://", "")).expanduser().resolve()
            if source.exists():
                shutil.copy2(source, target)
                return "stored", str(target)
            return "metadata_only", ""
        except Exception as exc:  # noqa: BLE001
            return f"error:{exc.__class__.__name__}", ""
