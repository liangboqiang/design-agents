from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


from wiki.adapter_bridge import WikiAdapterBridge
from ..render import WikiLinkRenderer
from ..search import WikiSearcher
from ..store import WikiStore


class SharedWikiService:
    """Unified Wiki Hub service for search, read, answer, and protocol-node materialization."""

    def __init__(self, *, project_root: Path, registry=None):  # noqa: ANN001
        self.project_root = Path(project_root).resolve()
        self.registry = registry
        self.store = WikiStore(self.project_root)
        self.wiki_guard = None

    def bind_permission_guard(self, wiki_guard) -> None:  # noqa: ANN001
        self.wiki_guard = wiki_guard

    def ensure_store(self) -> None:
        self.store.ensure()
        if not (self.store.read_catalog().get("pages") or {}):
            self.refresh_system()

    def refresh_system(self) -> str:
        self.store.ensure()
        nodes = WikiAdapterBridge(self.project_root).iter_nodes()
        entities = {
            node.node_id: {
                "kind": node.node_kind_hint or "knowledge",
                "title": node.title,
                "summary": node.summary,
                "path": node.source_path,
                "source_type": node.source_type,
                "links": node.links,
            }
            for node in nodes
        }
        catalog = {
            "pages": {
                node.node_id: {
                    "title": node.title,
                    "summary": node.summary,
                    "path": node.source_path,
                    "source_type": node.source_type,
                }
                for node in nodes
            }
        }
        graph = {
            "edges": [
                {"from": node.node_id, "to": link, "kind": "wiki_link"}
                for node in nodes
                for link in node.links
            ]
        }
        self.store.write_index({"entities": entities})
        self.store.write_catalog(catalog)
        self.store.write_graph(graph)
        job_id = f"refresh_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        self.store.write_job(job_id, {"job_id": job_id, "kind": "refresh_system", "node_count": len(nodes)})
        return json.dumps({"status": "ok", "nodes": len(nodes), "root": str(self.store.root)}, ensure_ascii=False, indent=2)

    def ingest_user_files(self, files: list[dict]) -> str:
        self.store.ensure()
        created: list[dict[str, str]] = []
        for index, item in enumerate(files or [], start=1):
            name = str(item.get("name") or item.get("filename") or item.get("path") or f"user_file_{index}")
            uri = str(item.get("url") or item.get("path") or "")
            status, stored_path = self._store_attachment(name=name, uri=uri)
            created.append({"name": name, "status": status, "stored_path": stored_path})
        return json.dumps({"status": "ok", "files": created}, ensure_ascii=False, indent=2)

    def search(self, query: str, limit: int = 20) -> str:
        self.ensure_store()
        searcher = WikiSearcher(store=self.store, read_text=self._read_repo_text)
        rows = searcher.search(query, limit=limit)
        if self.wiki_guard is not None:
            rows = self.wiki_guard.filter_rows(rows)
        return json.dumps(rows, ensure_ascii=False, indent=2)

    def read_page(self, page_id: str) -> str:
        self.ensure_store()
        if self.wiki_guard is not None:
            self.wiki_guard.require_read_page(page_id)
        catalog = self.store.read_catalog()
        row = (catalog.get("pages") or {}).get(page_id)
        if row is None:
            return f"Wiki Page not found: {page_id}"
        text = self._read_repo_text(str(row.get("path") or ""))
        renderer = WikiLinkRenderer(index=self.store.read_index(), catalog=catalog)
        return renderer.render(text)

    def read_source(self, page_id: str) -> str:
        return self.read_page(page_id)

    def answer(self, query: str, limit: int = 5) -> str:
        rows = json.loads(self.search(query, limit=limit))
        if not rows:
            return f"No wiki pages matched query: {query}"
        body = [f"# Wiki answer for: {query}", ""]
        for row in rows:
            body.append(f"## {row.get('title')}")
            body.append(str(row.get("summary") or ""))
            body.append(f"- Source: {row.get('path') or row.get('source_path')}")
            body.append("")
        return "\n".join(body).strip()

    def system_brief(self) -> str:
        self.ensure_store()
        catalog = self.store.read_catalog()
        return f"Unified Wiki Hub: {len(catalog.get('pages') or {})} Wiki Page node(s) searchable."

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
                import requests
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
