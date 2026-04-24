from __future__ import annotations


class WikiLinkResolver:
    def __init__(self, *, index: dict, catalog: dict):
        self.index = dict(index.get("entities") or {})
        self.catalog = dict(catalog.get("pages") or {})

    def describe(self, target: str) -> dict[str, str] | None:
        row = self.catalog.get(target) or self.index.get(target)
        if row is None:
            return None
        title = str(row.get("title") or target)
        summary = str(row.get("summary") or "").strip()
        path = str(row.get("path") or "")
        return {"title": title, "summary": summary, "path": path}
