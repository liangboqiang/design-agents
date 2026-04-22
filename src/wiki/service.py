from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

from .materializer import build_page_markdown, make_page
from .planner import plan_registry_tasks
from .store import WikiStore


class SharedWikiService:
    """Shared persistent wiki service.

    The shared wiki store lives under ``data/wiki`` and is independent from a
    specific runtime session. Build and refresh operations use the governance
    layer's generic ``agent_build`` skill through ``subagent.batch_run``.
    """

    AGENT_BUILD_SKILL = "governance/agent_build"

    def __init__(self, *, project_root: Path, registry):  # noqa: ANN001
        self.project_root = Path(project_root).resolve()
        self.registry = registry
        self.store = WikiStore(self.project_root)

    def ensure_store(self) -> None:
        self.store.ensure()

    def refresh_system(self, *, engine) -> str:  # noqa: ANN001
        self.ensure_store()
        tasks = plan_registry_tasks(self.project_root, self.registry, self.AGENT_BUILD_SKILL)
        job_id = f"wiki_refresh_{uuid.uuid4().hex[:12]}"

        jobs = [
            {
                "prompt": task.prompt,
                "skill": self.AGENT_BUILD_SKILL,
                "enhancements": [],
                "toolboxes": [],
                "role_name": f"wiki_extract_{index + 1:04d}",
            }
            for index, task in enumerate(tasks)
        ]

        payload_text = engine.dispatcher.dispatch(
            "subagent.batch_run",
            {
                "jobs": jobs,
                "max_workers": min(8, max(1, len(jobs))) if jobs else 1,
            },
        )
        payload = json.loads(payload_text)
        results = payload.get("results") or []

        existing_catalog = self.store.read_catalog()
        preserved_pages = [
            row
            for row in existing_catalog.get("pages") or []
            if str(row.get("source_kind") or "") == "user_file"
        ]

        built_pages: list[dict] = []
        failures: list[dict] = []

        for task, result in zip(tasks, results):
            if not result or not result.get("ok"):
                failures.append(
                    {
                        "task_id": task.task_id,
                        "source_id": task.source_id,
                        "error": (result or {}).get("error", "unknown error"),
                    }
                )
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
            built_pages.append(page.to_catalog_entry())

        catalog = {
            "pages": [*preserved_pages, *built_pages],
            "jobs": [
                *list(existing_catalog.get("jobs") or []),
                {
                    "job_id": job_id,
                    "kind": "refresh_system",
                    "skill": self.AGENT_BUILD_SKILL,
                    "page_count": len(built_pages),
                    "failure_count": len(failures),
                    "failures": failures,
                },
            ][-20:],
        }
        self.store.write_catalog(catalog)
        self.store.write_job(
            job_id,
            {
                "job_id": job_id,
                "kind": "refresh_system",
                "skill": self.AGENT_BUILD_SKILL,
                "task_count": len(tasks),
                "page_count": len(built_pages),
                "failure_count": len(failures),
                "failures": failures,
            },
        )

        return json.dumps(
            {
                "status": "ok",
                "root": str(self.store.root),
                "catalog_path": str(self.store.catalog_path),
                "pages": len(built_pages),
                "failures": len(failures),
            },
            ensure_ascii=False,
            indent=2,
        )

    def ingest_user_files(self, files: list[dict]) -> str:
        self.ensure_store()
        catalog = self.store.read_catalog()
        pages = [row for row in catalog.get("pages") or [] if str(row.get("source_kind") or "") != "user_file"]
        added: list[str] = []

        for index, item in enumerate(files or [], start=1):
            name = str(item.get("name") or item.get("filename") or item.get("path") or f"user_file_{index}")
            uri = str(item.get("url") or item.get("path") or "")
            page_id = hashlib.sha1(f"{name}|{uri}".encode("utf-8")).hexdigest()[:16]
            page = {
                "page_id": page_id,
                "source_id": f"user:{name}",
                "title": name,
                "summary": f"User-provided file: {name}",
                "key_points": [],
                "source_kind": "user_file",
                "source_path": str(item.get("path") or ""),
                "source_uri": uri,
                "source_hash": "",
                "tags": ["user", "attachment"],
                "updated_at": "",
                "metadata": {"raw": item},
            }
            pages.append(page)
            self.store.write_page(
                page_id,
                f"# {name}\n\n## Summary\n\nUser-provided file placeholder.\n\n## Source\n\n- URI: `{uri}`\n",
            )
            added.append(name)

        catalog["pages"] = pages
        self.store.write_catalog(catalog)
        return json.dumps({"status": "ok", "ingested": len(added), "files": added}, ensure_ascii=False, indent=2)

    def search(self, query: str, limit: int = 20) -> str:
        self.ensure_store()
        query = str(query or "").strip().lower()
        limit = max(1, int(limit or 20))
        pages = self.store.read_catalog().get("pages") or []

        scored = []
        tokens = [token for token in query.split() if token]
        for row in pages:
            hay = " ".join(
                [
                    str(row.get("title") or ""),
                    str(row.get("summary") or ""),
                    " ".join(str(item) for item in row.get("key_points") or []),
                    " ".join(str(item) for item in row.get("tags") or []),
                    str(row.get("source_path") or ""),
                ]
            ).lower()
            score = sum(1 for token in tokens if token in hay)
            if score > 0 or not tokens:
                scored.append((score, row))

        scored.sort(key=lambda item: (-item[0], str(item[1].get("title") or "")))
        return json.dumps([row for _, row in scored[:limit]], ensure_ascii=False, indent=2)

    def read_page(self, page_id: str) -> str:
        self.ensure_store()
        return self.store.read_page(page_id)

    def read_source(self, page_id: str) -> str:
        self.ensure_store()
        catalog = self.store.read_catalog()
        for row in catalog.get("pages") or []:
            if row.get("page_id") != page_id:
                continue
            source_path = str(row.get("source_path") or "").strip()
            source_uri = str(row.get("source_uri") or "").strip()
            if source_path:
                path = (self.project_root / source_path).resolve()
                if path.exists():
                    return path.read_text(encoding="utf-8")
                return f"Source missing: {source_path}"
            if source_uri.startswith("file://"):
                path = Path(source_uri[len("file://") :]).resolve()
                if path.exists():
                    return path.read_text(encoding="utf-8")
                return f"Source missing: {source_uri}"
            return "Source path is empty."
        return f"Page not found: {page_id}"

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
        self.ensure_store()
        catalog = self.store.read_catalog()
        issues = []
        for row in catalog.get("pages") or []:
            page_id = str(row.get("page_id") or "")
            if not page_id:
                issues.append({"page_id": page_id, "reason": "empty page_id"})
                continue
            if not self.store.page_path(page_id).exists():
                issues.append({"page_id": page_id, "reason": "page file missing"})
        return json.dumps({"status": "ok", "issues": issues}, ensure_ascii=False, indent=2)

    def system_brief(self) -> str:
        self.ensure_store()
        catalog = self.store.read_catalog()
        return f"Shared wiki store: {len(catalog.get('pages') or [])} page(s) available under data/wiki."

    @staticmethod
    def _parse_worker_payload(text: str) -> dict:
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    pass
        return {
            "title": "Untitled",
            "summary": text[:1000],
            "key_points": [],
            "tags": [],
        }
