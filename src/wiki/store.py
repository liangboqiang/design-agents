from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class WikiStore:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.root = self.project_root / "data" / "wiki"
        self.pages_dir = self.root / "pages"
        self.jobs_dir = self.root / "jobs"
        self.attachments_dir = self.root / "attachments"
        self.catalog_path = self.root / "catalog.json"

    def ensure(self) -> None:
        self.pages_dir.mkdir(parents=True, exist_ok=True)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.attachments_dir.mkdir(parents=True, exist_ok=True)
        if not self.catalog_path.exists():
            self.write_catalog({"pages": [], "jobs": []})

    def read_catalog(self) -> dict[str, Any]:
        self.ensure()
        return json.loads(self.catalog_path.read_text(encoding="utf-8"))

    def write_catalog(self, payload: dict[str, Any]) -> None:
        self.ensure()
        tmp = self.catalog_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.catalog_path)

    def page_path(self, page_id: str) -> Path:
        return self.pages_dir / f"{page_id}.md"

    def write_page(self, page_id: str, content: str) -> None:
        self.ensure()
        path = self.page_path(page_id)
        tmp = path.with_suffix(".md.tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(path)

    def read_page(self, page_id: str) -> str:
        return self.page_path(page_id).read_text(encoding="utf-8")

    def write_job(self, job_id: str, payload: dict[str, Any]) -> None:
        self.ensure()
        path = self.jobs_dir / f"{job_id}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
