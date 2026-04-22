from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Iterable

import yaml

from .config import WikiConfig

_HEADING_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_BULLET_RE = re.compile(r"^[-*]\s+(.+)$", re.MULTILINE)


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _nonempty_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _safe_text(path: Path, *, limit: int) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return text[:limit]


def summarize_file(path: Path, relpath: str, *, kind: str, config: WikiConfig) -> tuple[str, list[str], str, dict]:
    suffix = path.suffix.lower()
    text = _safe_text(path, limit=config.max_file_chars)
    if path.name == "SKILL.md":
        return _summarize_skill_markdown(path, relpath, text, config)
    if path.name.endswith(".agent.yaml"):
        return _summarize_agent_spec(path, relpath, text, config)
    if suffix == ".py":
        return _summarize_python(path, relpath, text, kind, config)
    if suffix in {".yaml", ".yml", ".json", ".toml"}:
        return _summarize_structured(path, relpath, text, kind, config)
    if suffix in {".md", ".markdown", ".txt", ".csv"}:
        return _summarize_text(path, relpath, text, kind, config)
    return (path.stem, [f"Source file: {relpath}"], _clip(text, config.max_excerpt_chars), {})


def _summarize_skill_markdown(path: Path, relpath: str, text: str, config: WikiConfig):
    meta, body = _split_frontmatter(text)
    title = str(meta.get("name") or path.parent.name)
    summary = [
        f"Skill id: {relpath.replace('/SKILL.md', '')}",
        f"Description: {str(meta.get('description') or '').strip() or 'No explicit description.'}",
    ]
    actions = [str(item) for item in meta.get("actions") or []]
    if actions:
        summary.append("Primary actions: " + ", ".join(actions[:8]))
    children = [str(item) for item in meta.get("children") or []]
    if children:
        summary.append("Child skills: " + ", ".join(children[:8]))
    excerpt = _clip(body.strip(), config.max_excerpt_chars)
    return title, summary[: config.max_summary_lines], excerpt, {"actions": actions, "children": children}


def _summarize_agent_spec(path: Path, relpath: str, text: str, config: WikiConfig):
    payload = yaml.safe_load(text) or {}
    title = str(payload.get("name") or path.stem)
    summary = [
        f"Agent spec: {title}",
        f"Root skill: {str(payload.get('root_skill') or 'unknown')}",
    ]
    toolboxes = [str(item) for item in payload.get("toolboxes") or []]
    capabilities = [str(item) for item in payload.get("capabilities") or []]
    if toolboxes:
        summary.append("Toolboxes: " + ", ".join(toolboxes[:8]))
    if capabilities:
        summary.append("Capabilities: " + ", ".join(capabilities[:8]))
    excerpt = _clip(text, config.max_excerpt_chars)
    return title, summary[: config.max_summary_lines], excerpt, {"toolboxes": toolboxes, "capabilities": capabilities}


def _summarize_python(path: Path, relpath: str, text: str, kind: str, config: WikiConfig):
    title = path.stem.replace("_", "-")
    summary: list[str] = [f"Python module: {relpath}"]
    meta: dict[str, object] = {}
    try:
        tree = ast.parse(text)
        doc = ast.get_docstring(tree)
        if doc:
            summary.append("Docstring: " + _clip(doc.splitlines()[0].strip(), 180))
        classes = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
        funcs = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
        if classes:
            summary.append("Classes: " + ", ".join(classes[:8]))
        if funcs:
            summary.append("Functions: " + ", ".join(funcs[:8]))
        meta = {"classes": classes, "functions": funcs}
    except SyntaxError:
        summary.append("Module could not be parsed by AST; stored as plain text summary.")
    excerpt = _clip(text, config.max_excerpt_chars)
    return title, summary[: config.max_summary_lines], excerpt, meta


def _summarize_structured(path: Path, relpath: str, text: str, kind: str, config: WikiConfig):
    title = path.stem.replace("_", "-")
    summary = [f"Structured file: {relpath}"]
    meta = {}
    try:
        if path.suffix.lower() in {".yaml", ".yml"}:
            payload = yaml.safe_load(text) or {}
        elif path.suffix.lower() == ".json":
            payload = json.loads(text or "{}")
        else:
            payload = {}
        if isinstance(payload, dict):
            keys = [str(key) for key in payload.keys()]
            if keys:
                summary.append("Top-level keys: " + ", ".join(keys[:10]))
            if "description" in payload:
                summary.append("Description: " + _clip(str(payload.get("description") or ""), 180))
            meta = {"keys": keys}
    except Exception:
        summary.append("Structured parse failed; stored as plain text summary.")
    excerpt = _clip(text, config.max_excerpt_chars)
    return title, summary[: config.max_summary_lines], excerpt, meta


def _summarize_text(path: Path, relpath: str, text: str, kind: str, config: WikiConfig):
    lines = _nonempty_lines(text)
    heading = _HEADING_RE.search(text)
    bullets = [match.group(1).strip() for match in _BULLET_RE.finditer(text)]
    title = heading.group(1).strip() if heading else path.stem.replace("_", "-")
    summary = [f"Text source: {relpath}"]
    if lines:
        summary.append("Lead: " + _clip(lines[0], 180))
    for bullet in bullets[: max(0, config.max_summary_lines - len(summary))]:
        summary.append(_clip(bullet, 180))
    excerpt = _clip(text, config.max_excerpt_chars)
    return title, summary[: config.max_summary_lines], excerpt, {"line_count": len(lines)}


def _split_frontmatter(text: str) -> tuple[dict, str]:
    stripped = text.strip()
    if not stripped.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return meta, body
