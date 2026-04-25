from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .node import WikiNode


LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
CODE_RE = re.compile(r"`([^`]+)`")


SECTION_ALIASES = {
    "overview": {"overview", "summary", "简介", "说明", "背景", "上下文", "context"},
    "capabilities": {"capabilities", "能力", "功能", "支持能力"},
    "usage": {"usage", "use", "使用方式", "适用场景", "何时使用", "context hint"},
    "runtime": {"runtime", "运行时", "协议", "system", "系统字段"},
    "tools": {"tools", "tool", "工具", "可用工具", "调用工具", "能力工具"},
    "links": {"links", "refs", "related", "related pages", "相关", "引用", "关联节点"},
    "root": {"root", "root skill", "根技能"},
    "children": {"child nodes", "child skills", "children", "子技能"},
    "policy": {"policy", "策略", "权限", "permission", "activation"},
    "input": {"input", "schema", "参数", "输入", "入参"},
    "output": {"output", "返回", "输出", "出参"},
    "safety": {"safety", "安全", "边界", "约束", "风险"},
    "toolbox": {"toolbox", "toolboxes", "工具箱"},
    "category": {"category", "categories", "分类"},
}


def normalize_section_title(title: str) -> str:
    raw = title.strip()
    low = raw.lower()
    for canonical, aliases in SECTION_ALIASES.items():
        if low in aliases or raw in aliases:
            return canonical
    return low


def extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.strip().startswith("# "):
            return line.strip()[2:].strip() or fallback
    return fallback.replace("_", " ").replace("-", " ").title()


def split_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {"__root__": []}
    current = "__root__"
    for line in text.splitlines():
        match = HEADING_RE.match(line.strip())
        if match and len(match.group(1)) == 2:
            current = normalize_section_title(match.group(2))
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items() if key != "__root__" and "\n".join(value).strip()}


def first_paragraph(text: str) -> str:
    rows: list[str] = []
    started = False
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("- [["):
            if started:
                break
            continue
        if s.startswith("```"):
            continue
        started = True
        rows.append(s)
    return " ".join(rows)[:400].strip()


def extract_runtime_block(sections: dict[str, str]) -> dict[str, object]:
    body = sections.get("runtime", "")
    payload: dict[str, object] = {}
    current_key = ""
    for line in body.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("- "):
            item = s[2:].strip()
            if ":" in item:
                key, value = item.split(":", 1)
                current_key = key.strip()
                value = value.strip().strip("`")
                if value:
                    payload[current_key] = _clean_value(value)
                else:
                    payload[current_key] = []
            elif current_key:
                payload.setdefault(current_key, [])
                if isinstance(payload[current_key], list):
                    payload[current_key].append(_clean_value(item.strip("`")))
        elif current_key and s.startswith("  - "):
            payload.setdefault(current_key, [])
            if isinstance(payload[current_key], list):
                payload[current_key].append(_clean_value(s[4:].strip("`")))
    return payload


def _clean_value(value: str) -> object:
    value = value.strip()
    if value.startswith("[[") and value.endswith("]]"):
        return value[2:-2].strip()
    if value.isdigit():
        return int(value)
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    return value


class WikiAdapterBridge:
    """Single node stream for system Wiki Pages and materialized Wiki Store nodes."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.src_root = self.project_root / "src"

    def iter_nodes(self) -> list[WikiNode]:
        nodes: list[WikiNode] = []
        for path in sorted(self.src_root.rglob("*.md")):
            if "__pycache__" in path.parts:
                continue
            rel = path.relative_to(self.project_root).as_posix()
            if rel.startswith("src/wiki/store/"):
                continue
            text = path.read_text(encoding="utf-8")
            sections = split_sections(text)
            node_id = self._node_id(path)
            nodes.append(
                WikiNode(
                    node_id=node_id,
                    title=extract_title(text, path.parent.name),
                    body=text,
                    summary=first_paragraph(text),
                    source_path=rel,
                    source_type="system",
                    node_kind_hint=self._kind_hint(path),
                    links=sorted(dict.fromkeys(LINK_RE.findall(text))),
                    sections=sections,
                    runtime_block=extract_runtime_block(sections),
                )
            )
        return nodes

    def _node_id(self, path: Path) -> str:
        rel_folder = path.parent.relative_to(self.src_root).as_posix()
        if path.name == "wiki.md":
            return rel_folder
        return f"wiki/{path.relative_to(self.src_root).as_posix()}"

    def _kind_hint(self, path: Path) -> str:
        parts = path.parent.relative_to(self.src_root).parts
        if not parts:
            return "knowledge"
        if parts[0] == "agent":
            return "agent"
        if parts[0] == "skill":
            return "skill"
        if parts[0] == "tool":
            if len(parts) >= 3 and parts[1] in {"external", "workflow", "system"}:
                return "toolbox" if len(parts) == 3 else "tool"
            return "tool"
        if parts[0] == "wiki":
            return "knowledge"
        return parts[0]
