from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
CODE_RE = re.compile(r"`([^`]+)`")


@dataclass(slots=True)
class ProtocolNode:
    node_id: str
    kind: str
    title: str
    path: str
    folder: str
    truth_ext: list[str]
    links: list[str]
    content_hash: str
    is_entity: bool


@dataclass(slots=True)
class ProtocolIndexResult:
    entities: dict[str, ProtocolNode] = field(default_factory=dict)
    pages: dict[str, ProtocolNode] = field(default_factory=dict)
    edges: list[dict[str, str]] = field(default_factory=list)

    def to_index_payload(self) -> dict[str, Any]:
        return {
            "entities": {
                node_id: {
                    "kind": node.kind,
                    "title": node.title,
                    "path": node.path,
                    "folder": node.folder,
                    "truth_ext": node.truth_ext,
                    "links": node.links,
                    "content_hash": node.content_hash,
                }
                for node_id, node in sorted(self.entities.items())
            }
        }

    def to_catalog_payload(self) -> dict[str, Any]:
        rows: dict[str, dict[str, str]] = {}
        for node_id, node in {**self.pages, **self.entities}.items():
            rows[node_id] = {
                "title": node.title,
                "path": node.path,
            }
        return {"pages": {node_id: rows[node_id] for node_id in sorted(rows)}}

    def to_graph_payload(self) -> dict[str, Any]:
        edges = sorted(self.edges, key=lambda row: (row["from"], row["to"], row["kind"]))
        return {"edges": edges}


def extract_markdown_links(text: str) -> list[str]:
    return [item.strip() for item in LINK_RE.findall(text) if item.strip()]


def extract_markdown_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            if title:
                return title
    return fallback.replace("_", " ").replace("-", " ").strip() or fallback


def first_paragraph(text: str) -> str:
    body_lines: list[str] = []
    started = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if not stripped and started:
            break
        if not stripped:
            continue
        started = True
        body_lines.append(stripped)
    return " ".join(body_lines).strip()


def split_markdown_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = "__root__"
    sections[current] = []
    for line in text.splitlines():
        match = HEADING_RE.match(line.strip())
        if match:
            level, title = match.groups()
            if len(level) == 2:
                current = title.strip()
                sections.setdefault(current, [])
                continue
        sections.setdefault(current, []).append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items()}


def extract_section_code_items(text: str) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        codes = [item.strip() for item in CODE_RE.findall(stripped) if item.strip()]
        if codes:
            items.extend(codes)
            continue
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


class ProtocolIndexer:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.src_root = self.project_root / "src"
        self.store_root = self.src_root / "wiki_store"
        self.index_path = self.store_root / "index.json"
        self.catalog_path = self.store_root / "catalog.json"
        self.graph_path = self.store_root / "graph.json"

    def scan(self) -> ProtocolIndexResult:
        result = ProtocolIndexResult()
        for folder in self._iter_folders():
            markdowns = sorted(path for path in folder.iterdir() if path.is_file() and path.suffix.lower() == ".md")
            if len(markdowns) != 1:
                continue
            markdown = markdowns[0]
            node = self._build_node(folder, markdown)
            if node.is_entity:
                result.entities[node.node_id] = node
            else:
                result.pages[node.node_id] = node

        valid_targets = set(result.entities) | set(result.pages)
        for node_id, node in {**result.entities, **result.pages}.items():
            for link in node.links:
                if link in valid_targets:
                    result.edges.append({"from": node_id, "to": link, "kind": "link"})
        return result

    def refresh_store(self) -> ProtocolIndexResult:
        result = self.scan()
        self.store_root.mkdir(parents=True, exist_ok=True)
        (self.store_root / "jobs").mkdir(parents=True, exist_ok=True)
        (self.store_root / "attachments").mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps(result.to_index_payload(), ensure_ascii=False, indent=2), encoding="utf-8")
        self.catalog_path.write_text(json.dumps(result.to_catalog_payload(), ensure_ascii=False, indent=2), encoding="utf-8")
        self.graph_path.write_text(json.dumps(result.to_graph_payload(), ensure_ascii=False, indent=2), encoding="utf-8")
        return result

    def load_store(self) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        return (
            self._read_json(self.index_path, {"entities": {}}),
            self._read_json(self.catalog_path, {"pages": {}}),
            self._read_json(self.graph_path, {"edges": []}),
        )

    def _iter_folders(self):
        if not self.src_root.exists():
            return
        for folder in sorted(self.src_root.rglob("*")):
            if not folder.is_dir():
                continue
            if folder == self.store_root:
                continue
            if "__pycache__" in folder.parts:
                continue
            yield folder

    def _build_node(self, folder: Path, markdown: Path) -> ProtocolNode:
        rel_folder = folder.relative_to(self.src_root).as_posix()
        kind = rel_folder.split("/", 1)[0]
        is_entity = markdown.name == f"{kind}.md"
        node_id = rel_folder if is_entity else f"page/{rel_folder}"
        text = markdown.read_text(encoding="utf-8")
        truth_ext = sorted(
            file.name for file in folder.iterdir() if file.is_file() and file.suffix.lower() != ".md"
        )
        links = sorted(dict.fromkeys(extract_markdown_links(text)))
        content_hash = self._content_hash([markdown, *(folder / name for name in truth_ext)])
        return ProtocolNode(
            node_id=node_id,
            kind=kind if is_entity else "page",
            title=extract_markdown_title(text, folder.name),
            path=str(markdown.relative_to(self.project_root).as_posix()),
            folder=str(folder.relative_to(self.project_root).as_posix()),
            truth_ext=truth_ext,
            links=links,
            content_hash=content_hash,
            is_entity=is_entity,
        )

    @staticmethod
    def _content_hash(paths: list[Path]) -> str:
        digest = hashlib.sha1()
        for path in paths:
            digest.update(path.name.encode("utf-8"))
            try:
                digest.update(path.read_bytes())
            except OSError:
                continue
        return digest.hexdigest()

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
