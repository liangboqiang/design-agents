from __future__ import annotations

import hashlib
import json
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
CODE_RE = re.compile(r"`([^`]+)`")
PURE_LINK_LINE_RE = re.compile(r"^(?:[-*+]\s+)?(?:\[\[[^\]]+\]\]\s*)+$")

SECTION_TITLE_ALIASES = {
    "actions": "actions",
    "capabilities": "capabilities",
    "child skills": "child skills",
    "children": "child skills",
    "context": "context",
    "context policy": "context policy",
    "implementation": "implementation",
    "llm": "llm",
    "refs": "refs",
    "related": "refs",
    "related pages": "related pages",
    "root skill": "root skill",
    "toolboxes": "toolboxes",
    "tools": "tools",
    "使用动作": "actions",
    "使用工具": "tools",
    "入口动作": "actions",
    "入口工具": "tools",
    "上下文策略": "context policy",
    "子技能": "child skills",
    "实现": "implementation",
    "工具箱": "toolboxes",
    "动作": "actions",
    "协同工具": "tools",
    "引用": "refs",
    "根技能": "root skill",
    "相关内容": "refs",
    "相关页面": "related pages",
    "能力": "capabilities",
}

SETTINGS_FILENAMES = ("runtime.toml", "profile.env", "overrides.json")
GENERATED_STORE_FILENAMES = {"catalog.json", "graph.json", "index.json"}

GENERIC_SUMMARY_PATTERNS = (
    re.compile(r"^skill page for\b", re.IGNORECASE),
    re.compile(r"^agent page for\b", re.IGNORECASE),
    re.compile(r"^canonical tool page for\b", re.IGNORECASE),
    re.compile(r"^context page for\b", re.IGNORECASE),
)

TOOL_SUMMARY_OVERRIDES = {
    "compact.now": "Compact the current conversation state into the summary context.",
    "engine.enter_skill": "Enter a reachable skill and switch the active runtime scope.",
    "engine.inspect_action": "Inspect one action that is currently available in the runtime surface.",
    "engine.inspect_skill": "Inspect a reachable skill and its surfaced behavior.",
    "engine.list_child_skills": "List the child skills that can be entered from the current skill.",
    "files.edit_text": "Edit text content inside a workspace file.",
    "files.list_dir": "List files and folders in the current workspace.",
    "files.read_text": "Read text content from a workspace file.",
    "files.write_text": "Write text content to a workspace file.",
    "governance.inspect_tool_surface": "Inspect the visible tool surface and exposed actions.",
    "governance.load_refs": "Load referenced skills into the active governed surface.",
    "governance.normalize_tool_result": "Normalize tool outputs into a cleaner runtime result format.",
    "protocol.request_shutdown": "Request a governed shutdown handshake for the current run.",
    "protocol.respond_shutdown": "Respond to a governed shutdown request.",
    "protocol.review_plan": "Review a proposed execution plan before continuing work.",
    "protocol.submit_plan": "Submit a plan for governed review and tracking.",
    "shell.run": "Run a shell command in the current workspace.",
    "subagent.ask": "Delegate one focused question to a subagent.",
    "subagent.batch_run": "Run a batch of subagent jobs in one coordinated pass.",
    "task.claim": "Claim a task from the shared task queue.",
    "task.create": "Create a task in the shared task queue.",
    "task.get": "Read one task from the shared task queue.",
    "task.list": "List tasks from the shared task queue.",
    "task.update": "Update an existing task in the shared task queue.",
    "team.read_inbox": "Read messages from the shared team inbox.",
    "todo.update": "Update the runtime todo list.",
    "todo.view": "Read the current runtime todo list.",
    "wiki.answer": "Draft an answer from the shared wiki store.",
    "wiki.read_page": "Read one rendered page from the shared wiki store.",
    "wiki.read_source": "Read the original source text behind a wiki page.",
    "wiki.search": "Search pages in the shared wiki store.",
    "wiki_admin.ingest_files": "Ingest user-provided files into the shared wiki store.",
    "wiki_admin.lint": "Lint the shared wiki store and protocol links.",
    "wiki_admin.refresh_system": "Refresh the shared wiki index and system summaries.",
    "workspace.create": "Create a workspace for the current task.",
    "workspace.keep": "Persist the current workspace for later reuse.",
    "workspace.list": "List available task workspaces.",
    "workspace.remove": "Remove a task workspace that is no longer needed.",
    "workspace.run": "Run a command inside a task workspace.",
}


@dataclass(slots=True)
class ProtocolNode:
    node_id: str
    kind: str
    title: str
    summary: str
    path: str
    folder: str
    truth_ext: list[str]
    links: list[str]
    content_hash: str
    is_entity: bool
    runtime_action: str | None = None
    section_map: dict[str, str] = field(default_factory=dict)
    section_links: dict[str, list[str]] = field(default_factory=dict)
    code_items: dict[str, list[str]] = field(default_factory=dict)
    settings: dict[str, str] = field(default_factory=dict)


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
                    "summary": node.summary,
                    "path": node.path,
                    "folder": node.folder,
                    "truth_ext": node.truth_ext,
                    "links": node.links,
                    "content_hash": node.content_hash,
                    "runtime_action": node.runtime_action,
                    "section_map": node.section_map,
                    "section_links": node.section_links,
                    "code_items": node.code_items,
                    "settings": node.settings,
                }
                for node_id, node in sorted(self.entities.items())
            }
        }

    def to_catalog_payload(self) -> dict[str, Any]:
        rows: dict[str, dict[str, str]] = {}
        for node_id, node in {**self.pages, **self.entities}.items():
            rows[node_id] = {
                "kind": node.kind,
                "title": node.title,
                "summary": node.summary,
                "path": node.path,
            }
        return {"pages": {node_id: rows[node_id] for node_id in sorted(rows)}}

    def to_graph_payload(self) -> dict[str, Any]:
        edges = sorted(self.edges, key=lambda row: (row["from"], row["to"], row["kind"]))
        return {"edges": edges}


def extract_markdown_links(text: str) -> list[str]:
    without_fences = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    sanitized = re.sub(r"`[^`\n]+`", "", without_fences)
    return [item.strip() for item in LINK_RE.findall(sanitized) if item.strip()]


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
        if stripped.startswith("```"):
            continue
        if PURE_LINK_LINE_RE.fullmatch(stripped):
            if started:
                break
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


def normalize_section_title(title: str) -> str:
    stripped = title.strip()
    if not stripped:
        return stripped
    return SECTION_TITLE_ALIASES.get(stripped, SECTION_TITLE_ALIASES.get(stripped.lower(), stripped.lower()))


def extract_section_links(text: str) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in extract_markdown_links(text):
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def clip_summary(text: str, limit: int = 120) -> str:
    collapsed = re.sub(r"\s+", " ", text).strip()
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3].rstrip() + "..."


def humanize_identifier(value: str) -> str:
    parts = [part for part in re.split(r"[_\-/]+", value.strip()) if part]
    return " ".join(part.capitalize() for part in parts)


def tool_link_to_action_id(link: str) -> str:
    parts = link.split("/")
    if len(parts) < 3:
        return link.replace("/", ".")
    return ".".join(parts[1:])


def tool_title_from_node_id(node_id: str) -> str:
    return humanize_identifier(node_id.removeprefix("tool/"))


def should_replace_tool_title(title: str) -> bool:
    normalized = title.strip()
    return "." in normalized or normalized.lower().startswith("canonical ")


def describe_tool_node(node_id: str) -> str:
    action_id = tool_link_to_action_id(node_id)
    return TOOL_SUMMARY_OVERRIDES.get(action_id, f"Tool surface for {tool_title_from_node_id(node_id)}.")


def parse_truth_settings(folder: Path, truth_ext: list[str]) -> dict[str, str]:
    settings: dict[str, str] = {}
    for name in truth_ext:
        if name not in SETTINGS_FILENAMES:
            continue
        path = folder / name
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if name.endswith(".json"):
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                for key, value in payload.items():
                    if value is None:
                        continue
                    settings[str(key)] = str(value)
            continue
        if name.endswith(".toml"):
            try:
                payload = tomllib.loads(text)
            except tomllib.TOMLDecodeError:
                continue
            if isinstance(payload, dict):
                for key, value in payload.items():
                    if value is None:
                        continue
                    settings[str(key)] = str(value)
            continue
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            if key and value:
                settings[key] = value
    return settings


def build_structured_sections(text: str) -> tuple[dict[str, str], dict[str, list[str]], dict[str, list[str]]]:
    raw_sections = split_markdown_sections(text)
    section_map: dict[str, str] = {}
    for raw_title, body in raw_sections.items():
        if raw_title == "__root__":
            continue
        title = normalize_section_title(raw_title)
        body = body.strip()
        if not title or not body:
            continue
        if title in section_map:
            section_map[title] = f"{section_map[title]}\n\n{body}".strip()
        else:
            section_map[title] = body

    section_links = {title: extract_section_links(body) for title, body in section_map.items()}
    code_items = {title: extract_section_code_items(body) for title, body in section_map.items()}
    code_items = {title: items for title, items in code_items.items() if items}
    return section_map, section_links, code_items


def _is_generic_summary(text: str) -> bool:
    return any(pattern.search(text) for pattern in GENERIC_SUMMARY_PATTERNS)


def build_node_summary(
    *,
    node_id: str,
    kind: str,
    title: str,
    lead: str,
    section_links: dict[str, list[str]],
    code_items: dict[str, list[str]],
) -> str:
    if lead and not _is_generic_summary(lead):
        return clip_summary(lead)
    if kind == "tool":
        return clip_summary(describe_tool_node(node_id))
    if kind == "skill":
        parts: list[str] = []
        tool_count = len(section_links.get("tools", []))
        child_count = len(section_links.get("child skills", []))
        ref_count = len(section_links.get("refs", []))
        if tool_count:
            parts.append(f"Uses {tool_count} tool(s).")
        if child_count:
            parts.append(f"Exposes {child_count} child skill(s).")
        if ref_count:
            parts.append(f"References {ref_count} related skill(s).")
        if parts:
            return clip_summary(" ".join(parts))
        return clip_summary(f"Skill page for {title}.")
    if kind == "agent":
        parts = [f"Agent entrypoint for {title}."]
        root_skill = next((item for item in section_links.get("root skill", []) if item.startswith("skill/")), "")
        if root_skill:
            parts.append(f"Root skill: {humanize_identifier(root_skill.removeprefix('skill/'))}.")
        if code_items.get("toolboxes"):
            parts.append(f"Toolboxes: {len(code_items['toolboxes'])}.")
        if code_items.get("capabilities"):
            parts.append(f"Capabilities: {len(code_items['capabilities'])}.")
        return clip_summary(" ".join(parts))
    if kind == "context":
        return clip_summary(f"Context asset for {title}.")
    return clip_summary(lead or f"{kind.capitalize()} page for {title}.")


class ProtocolIndexer:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.src_root = self.project_root / "src"
        self.store_root = self.src_root / "wiki/store"
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
            if "__pycache__" in folder.parts:
                continue
            yield folder

    def _build_node(self, folder: Path, markdown: Path) -> ProtocolNode:
        rel_folder = folder.relative_to(self.src_root).as_posix()
        kind = rel_folder.split("/", 1)[0]
        is_entity = markdown.name == "page.md"
        node_id = rel_folder if is_entity else f"page/{rel_folder}"
        text = markdown.read_text(encoding="utf-8")
        truth_ext = sorted(
            file.name
            for file in folder.iterdir()
            if file.is_file() and file.suffix.lower() != ".md" and not self._is_generated_store_file(folder, file)
        )
        section_map, section_links, code_items = build_structured_sections(text)
        runtime_action = tool_link_to_action_id(node_id) if kind == "tool" and is_entity else None
        title = extract_markdown_title(text, folder.name)
        if kind == "tool" and is_entity and should_replace_tool_title(title):
            title = tool_title_from_node_id(node_id)
        lead = first_paragraph(text)
        settings = parse_truth_settings(folder, truth_ext)
        links = sorted(dict.fromkeys(extract_markdown_links(text)))
        content_hash = self._content_hash([markdown, *(folder / name for name in truth_ext)])
        return ProtocolNode(
            node_id=node_id,
            kind=kind if is_entity else "page",
            title=title,
            summary=build_node_summary(
                node_id=node_id,
                kind=kind if is_entity else "page",
                title=title,
                lead=lead,
                section_links=section_links,
                code_items=code_items,
            ),
            path=str(markdown.relative_to(self.project_root).as_posix()),
            folder=str(folder.relative_to(self.project_root).as_posix()),
            truth_ext=truth_ext,
            links=links,
            content_hash=content_hash,
            is_entity=is_entity,
            runtime_action=runtime_action,
            section_map=section_map,
            section_links=section_links,
            code_items=code_items,
            settings=settings,
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

    def _is_generated_store_file(self, folder: Path, file: Path) -> bool:
        try:
            rel_folder = folder.relative_to(self.src_root).as_posix()
        except ValueError:
            return False
        return rel_folder == "wiki/store" and file.name in GENERATED_STORE_FILENAMES

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
