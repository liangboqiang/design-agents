from __future__ import annotations

import json
from pathlib import Path

from shared.paths import project_root

from .materializer import build_page_markdown, make_page
from .planner import plan_registry_tasks
from .store import WikiStore


class SharedWikiService:
    EXTRACTOR_SKILL = "governance/subagent_engine/extractor"

    def __init__(self, *, project_root: Path, registry):  # noqa: ANN001
        self.project_root = Path(project_root).resolve()
        self.registry = registry
        self.store = WikiStore(self.project_root)

    def ensure_store(self) -> None:
        self.store.ensure()

    def refresh_system(self, *, engine) -> str:  # noqa: ANN001
        self.ensure_store()
        tasks = plan_registry_tasks(self.project_root, self.registry, self.EXTRACTOR_SKILL)
        jobs = [
            {
                "prompt": task.prompt,
                "skill": self.EXTRACTOR_SKILL,
                "enhancements": [],
                "toolboxes": [],
                "role_name": f"wiki_extract_{index+1:04d}",
            }
            for index, task in enumerate(tasks)
        ]
        payload_text = engine.dispatcher.dispatch(
            "subagent.batch_run",
            {
                "jobs": jobs,
                "max_workers": 6,
            },
        )
        payload = json.loads(payload_text)
        results = payload.get("results") or []
        catalog_pages: list[dict] = []
        failures: list[dict] = []
        for task, result in zip(tasks, results):
            if not result or not result.get("ok"):
                failures.append({"task_id": task.task_id, "source_id": task.source_id, "error": (result or {}).get("error", "unknown error")})
                continue
            draft = self._parse_worker_payload(str(result.get("result") or ""))
            page = make_page(
                page_id=task.page_id,
                source_id=task.source_id,
                source_kind=task.source_kind,
                source_path=task.source_path,
                source_uri=task.source_uri,
                source_hash=str(task.metadata.get("source_hash") or ""),
                payload=draft,
                tags=task.tags,
            )
            self.store.write_page(page.page_id, build_page_markdown(page))
            catalog_pages.append(page.to_catalog_entry())
        catalog = {"pages": catalog_pages, "jobs": [{"kind": "refresh_system", "failures": failures, "page_count": len(catalog_pages)}]}
        self.store.write_catalog(catalog)
        return json.dumps({"status": "ok", "pages": len(catalog_pages), "failures": len(failures)}, ensure_ascii=False, indent=2)

    def ingest_user_files(self, files: list[dict]) -> str:
        self.ensure_store()
        if not files:
            return json.dumps({"status": "ok", "ingested": 0, "files": []}, ensure_ascii=False, indent=2)
        catalog = self.store.read_catalog()
        pages = list(catalog.get("pages") or [])
        added = []
        for index, item in enumerate(files, start=1):
            name = str(item.get("name") or item.get("filename") or item.get("path") or f"user_file_{index}")
            page_id = f"user_{abs(hash(name)) % 10_000_000:07d}"
            page = {
                "page_id": page_id,
                "source_id": f"user:{name}",
                "title": name,
                "summary": f"User-provided file: {name}",
                "key_points": [],
                "source_kind": "user_file",
                "source_path": str(item.get("path") or ""),
                "source_uri": str(item.get("url") or item.get("path") or ""),
                "source_hash": "",
                "tags": ["user", "attachment"],
                "updated_at": "",
                "metadata": {"raw": item},
            }
            pages = [row for row in pages if row.get("page_id") != page_id]
            pages.append(page)
            self.store.write_page(page_id, f"# {name}\n\nUser-provided file placeholder.\n")
            added.append(name)
        catalog["pages"] = pages
        self.store.write_catalog(catalog)
        return json.dumps({"status": "ok", "ingested": len(added), "files": added}, ensure_ascii=False, indent=2)

    def search(self, query: str) -> str:
        self.ensure_store()
        query = query.strip().lower()
        pages = self.store.read_catalog().get("pages") or []
        scored = []
        for row in pages:
            hay = " ".join(
                [
                    str(row.get("title") or ""),
                    str(row.get("summary") or ""),
                    " ".join(str(item) for item in row.get("tags") or []),
                    str(row.get("source_path") or ""),
                ]
            ).lower()
            score = 0
            for token in [token for token in query.split() if token]:
                if token in hay:
                    score += 1
            if score > 0 or not query:
                scored.append((score, row))
        scored.sort(key=lambda item: (-item[0], str(item[1].get("title") or "")))
        results = [row for _, row in scored[:20]]
        return json.dumps(results, ensure_ascii=False, indent=2)

    def read_page(self, page_id: str) -> str:
        self.ensure_store()
        return self.store.read_page(page_id)

    def read_source(self, page_id: str) -> str:
        self.ensure_store()
        catalog = self.store.read_catalog()
        for row in catalog.get("pages") or []:
            if row.get("page_id") != page_id:
                continue
            source_path = str(row.get("source_path") or "")
            if not source_path:
                return "Source path is empty."
            path = (self.project_root / source_path).resolve()
            if not path.exists():
                return f"Source missing: {source_path}"
            return path.read_text(encoding="utf-8")
        return f"Page not found: {page_id}"

    def answer(self, query: str, limit: int = 5) -> str:
        rows = json.loads(self.search(query))
        rows = rows[: max(1, int(limit))]
        if not rows:
            return f"No wiki pages matched query: {query}"
        body = [f"# Wiki answer for: {query}", ""]
        for row in rows:
            body.append(f"## {row.get('title')}")
            body.append(str(row.get("summary") or ""))
            points = row.get("key_points") or []
            for point in points[:5]:
                body.append(f"- {point}")
            body.append(f"- Source: {row.get('source_path')}")
            body.append("")
        return "\n".join(body).strip()

    def lint(self) -> str:
        self.ensure_store()
        catalog = self.store.read_catalog()
        missing = []
        for row in catalog.get("pages") or []:
            page_id = str(row.get("page_id") or "")
            if not page_id:
                missing.append({"page_id": page_id, "reason": "empty page_id"})
                continue
            if not self.store.page_path(page_id).exists():
                missing.append({"page_id": page_id, "reason": "page file missing"})
        return json.dumps({"status": "ok", "issues": missing}, ensure_ascii=False, indent=2)

    def system_brief(self) -> str:
        self.ensure_store()
        catalog = self.store.read_catalog()
        page_count = len(catalog.get("pages") or [])
        return f"Shared wiki store: {page_count} page(s) available under data/wiki."

    @staticmethod
    def _parse_worker_payload(text: str) -> dict:
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(text[start : end + 1])
        return {"title": "Untitled", "summary": text[:1000], "key_points": [], "tags": []}
