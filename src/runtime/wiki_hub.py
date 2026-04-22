from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
import yaml


WIKI_GROUPS = {
    "sources": "来源",
    "entities": "实体",
    "concepts": "概念",
    "comparisons": "对比",
    "skills": "技能",
    "tools": "工具",
    "agents": "智能体",
    "attachments": "附件",
    "system": "系统",
}


@dataclass(slots=True)
class SearchHit:
    path: str
    title: str
    score: int
    preview: str


def _utc_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    stripped = text.strip()
    if not stripped.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return meta, body


def _slugify(text: str) -> str:
    normalized = re.sub(r"[^\w\-./一-龥]+", "-", text.strip(), flags=re.UNICODE)
    normalized = normalized.strip("-").replace("/", "__")
    return normalized or "item"


def _titleize(path: Path) -> str:
    return path.stem.replace("_", " ").replace("-", " ").strip() or path.name


def _first_paragraph(text: str, limit: int = 360) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


def _extract_links(text: str) -> set[str]:
    return set(re.findall(r"\[\[([^\]]+)\]\]", text))


def _copy_text_or_note(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    except UnicodeDecodeError:
        dst.write_text(f"[binary-or-non-utf8] {src.name}", encoding="utf-8")


class WikiHub:
    def __init__(self, *, project_root: Path, registry, session, hub_name: str = "default"):  # noqa: ANN001
        self.project_root = project_root.resolve()
        self.registry = registry
        self.session = session
        user_root = session.paths.root.parents[1]
        self.root = (user_root / "_knowledge_hubs" / hub_name).resolve()
        self.raw_root = self.root / "raw"
        self.wiki_root = self.root / "wiki"
        self.schema_root = self.root / "schemas"
        self.state_root = self.root / "state"
        self.catalog_path = self.state_root / "catalog.json"
        self.schema_path = self.schema_root / "WIKI_SCHEMA.md"
        self.index_path = self.wiki_root / "index.md"
        self.log_path = self.wiki_root / "log.md"
        self.ensure_bootstrap()

    def ensure_bootstrap(self) -> None:
        for path in (
            self.raw_root / "business",
            self.raw_root / "system",
            self.raw_root / "users",
            self.schema_root,
            self.state_root,
            self.wiki_root,
        ):
            path.mkdir(parents=True, exist_ok=True)
        for dirname in WIKI_GROUPS.values():
            (self.wiki_root / dirname).mkdir(parents=True, exist_ok=True)
        if not self.schema_path.exists():
            self.schema_path.write_text(self._default_schema_text(), encoding="utf-8")
        if not self.index_path.exists():
            self.index_path.write_text("# Wiki Index\n\n初始化中。\n", encoding="utf-8")
        if not self.log_path.exists():
            self.log_path.write_text("", encoding="utf-8")
        if not self.catalog_path.exists():
            self._write_json(self.catalog_path, {"pages": {}, "raw_sources": {}, "last_refresh": None})

    def _default_schema_text(self) -> str:
        return """# LLM Wiki Schema

## 设计立场

- Wiki 是系统唯一知识中枢
- 但 Wiki 不是唯一知识来源
- Schema 是增强器，不是唯一真相
- 允许页面围绕真实资料野蛮生长，再由索引、链接、lint、日志收束

## 三类知识源

1. 业务资料源：每个 `SKILL.md` 同目录下的 `knowledge/`
2. 系统自描述源：skills / tools / agents / context / 关键程序逻辑
3. 用户输入源：消息与附件 `files[{name,url}]`

## 目录

- `raw/`：原始来源层
- `wiki/`：编译后的知识层
- `schemas/`：规则增强层
- `state/`：目录索引与编译状态

## 页面原则

- 来源页始终可创建
- 技能 / 工具 / 智能体 / 系统页允许自动生成
- 概念 / 实体 / 对比页允许逐步补全，不要求一开始完备
- frontmatter 是辅助追踪，不限制正文自然扩展
"""

    def refresh_from_registry(self) -> str:
        self.ensure_bootstrap()
        self.registry.refresh()
        catalog = self._read_json(self.catalog_path, {"pages": {}, "raw_sources": {}, "last_refresh": None})
        stats = {
            "business_sources": 0,
            "system_sources": 0,
            "skill_pages": 0,
            "tool_pages": 0,
            "agent_pages": 0,
            "attachment_pages": 0,
        }

        for skill in self.registry.skills.values():
            self._write_skill_page(skill)
            stats["skill_pages"] += 1
            for path in skill.knowledge_files:
                self._ingest_business_file(skill.skill_id, path)
                stats["business_sources"] += 1

        system_paths = self.registry.iter_system_source_files()
        for path in system_paths:
            self._mirror_system_raw(path)
            stats["system_sources"] += 1

        for toolbox_name, descriptor in sorted(self.registry.toolboxes.items()):
            self._write_toolbox_page(toolbox_name, descriptor)
            stats["tool_pages"] += 1

        for agent_name, spec in sorted(self.registry.agent_specs.items()):
            self._write_agent_page(agent_name, spec)
            stats["agent_pages"] += 1

        self._write_system_inventory_page(system_paths)
        self._sync_index()
        catalog["last_refresh"] = _utc_now()
        self._write_json(self.catalog_path, catalog)
        self._append_log("update", "refresh registry", stats)
        return json.dumps({"status": "ok", "stats": stats, "hub_root": str(self.root)}, ensure_ascii=False, indent=2)

    def ingest_user_files(self, files: list[dict[str, Any]] | None) -> str:
        if not files:
            return json.dumps({"status": "noop", "reason": "no files"}, ensure_ascii=False)
        self.ensure_bootstrap()
        created: list[dict[str, Any]] = []
        for item in files:
            name = str(item.get("name") or "").strip()
            url = str(item.get("url") or "").strip()
            if not name or not url:
                created.append({"name": name or "(missing)", "status": "skipped", "reason": "name/url required"})
                continue
            meta = self._persist_user_source(name=name, url=url)
            self._write_attachment_page(meta)
            created.append({"name": name, "status": meta["status"], "stored_path": meta.get("stored_path")})
        self._sync_index()
        self._append_log("ingest", "user files", {"count": len(created)})
        return json.dumps({"status": "ok", "files": created}, ensure_ascii=False, indent=2)

    def search(self, query: str, limit: int = 10, groups: list[str] | None = None) -> str:
        hits = self._search_hits(query=query, limit=limit, groups=groups)
        payload = [{"path": hit.path, "title": hit.title, "score": hit.score, "preview": hit.preview} for hit in hits]
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def read_page(self, page: str) -> str:
        target = self._resolve_page(page)
        return target.read_text(encoding="utf-8")

    def answer(self, query: str, limit: int = 5) -> str:
        hits = self._search_hits(query=query, limit=limit)
        if not hits:
            return f"No wiki pages matched query: {query}"
        chunks: list[str] = [f"# Wiki answer context\n\nquery: {query}\n"]
        for hit in hits:
            target = self._resolve_page(hit.path)
            _, body = _split_frontmatter(target.read_text(encoding="utf-8"))
            chunks.append(
                f"## {hit.title}\n"
                f"page: {hit.path}\n"
                f"score: {hit.score}\n"
                f"summary: {_first_paragraph(body, 800)}\n"
            )
        return "\n".join(chunks).strip()

    def lint(self) -> str:
        pages = list(self._iter_wiki_pages())
        existing = {self._relative_page_path(page) for page in pages}
        inbound_counts = {path: 0 for path in existing}
        broken_links: list[dict[str, str]] = []
        for page in pages:
            text = page.read_text(encoding="utf-8")
            current = self._relative_page_path(page)
            for link in _extract_links(text):
                normalized = self._normalize_link_target(link)
                if normalized in inbound_counts:
                    inbound_counts[normalized] += 1
                else:
                    broken_links.append({"from": current, "target": link})
        orphan_pages = [path for path, count in inbound_counts.items() if count == 0 and not path.endswith("index.md")]
        result = {
            "pages": len(pages),
            "broken_links": broken_links,
            "orphan_pages": orphan_pages,
            "index_exists": self.index_path.exists(),
        }
        self._append_log("lint", "wiki lint", {"broken_links": len(broken_links), "orphans": len(orphan_pages)})
        return json.dumps(result, ensure_ascii=False, indent=2)

    def system_brief(self) -> str:
        index_text = self.index_path.read_text(encoding="utf-8") if self.index_path.exists() else ""
        lines = [line for line in index_text.splitlines() if line.startswith("- ")]
        preview = "\n".join(lines[:8])
        return (
            f"Hub root: {self.root}\n"
            "Knowledge source policy:\n"
            "- business: skill-local knowledge/\n"
            "- system: repo self-description\n"
            "- user: attachments + turn input\n\n"
            f"Index preview:\n{preview}"
        )

    def _write_skill_page(self, skill) -> None:  # noqa: ANN001
        links = []
        for child in skill.children:
            links.append(f"- child: `[[技能/{_slugify(child)}]]`")
        for ref_id in skill.refs:
            links.append(f"- ref: `[[技能/{_slugify(ref_id)}]]`")
        for path in skill.knowledge_files:
            links.append(f"- business source: `[[来源/{_slugify(skill.skill_id + '__' + path.stem)}]]`")
        action_lines = [f"- `{action}`" for action in skill.actions] or ["- (none)"]
        link_lines = links or ["- (none)"]
        body = "\n".join(
            [
                f"# {skill.name}",
                "",
                f"- skill_id: `{skill.skill_id}`",
                f"- source: `[[raw/system/{self._raw_system_name(skill.markdown_path)}]]`",
                "",
                "## Summary",
                skill.description or "No description.",
                "",
                "## Actions",
                *action_lines,
                "",
                "## Links",
                *link_lines,
                "",
                "## Body",
                skill.markdown_body.strip() or "(empty)",
            ]
        )
        self._write_page(
            group="skills",
            page_name=_slugify(skill.skill_id),
            page_type="skill",
            tags=["skill", "system"],
            sources=[str(skill.markdown_path.relative_to(self.project_root).as_posix())],
            body=body,
        )
        self._mirror_system_raw(skill.markdown_path)

    def _write_toolbox_page(self, toolbox_name: str, descriptor) -> None:  # noqa: ANN001
        source_file = self._module_to_path(descriptor.module)
        if source_file is not None and source_file.exists():
            self._mirror_system_raw(source_file)
        body = "\n".join(
            [
                f"# {toolbox_name}",
                "",
                f"- module: `{descriptor.module}`",
                f"- class: `{descriptor.class_name}`",
                f"- discoverable: `{descriptor.discoverable}`",
                f"- tags: {', '.join(descriptor.tags) if descriptor.tags else '(none)'}",
                "",
                "## Position",
                "This page is part of the system self-description layer. It is not the final truth by itself; the wiki page is the compiled view.",
                "",
                "## Source",
                f"- `[[raw/system/{self._raw_system_name(source_file)}]]`" if source_file else "- unavailable",
            ]
        )
        self._write_page(
            group="tools",
            page_name=_slugify(toolbox_name),
            page_type="tool",
            tags=["tool", "system"],
            sources=[descriptor.module],
            body=body,
        )

    def _write_agent_page(self, agent_name: str, spec) -> None:  # noqa: ANN001
        source_file = self.project_root / spec.source_path if spec.source_path else None
        if source_file and source_file.exists():
            self._mirror_system_raw(source_file)
        toolbox_lines = [f"- `[[工具/{_slugify(name)}]]`" for name in spec.toolboxes] or ["- (none)"]
        capability_lines = [f"- `{name}`" for name in spec.capabilities] or ["- (none)"]
        body = "\n".join(
            [
                f"# {agent_name}",
                "",
                f"- root_skill: `[[技能/{_slugify(spec.root_skill)}]]`",
                "",
                "## Description",
                spec.description or "(none)",
                "",
                "## Toolboxes",
                *toolbox_lines,
                "",
                "## Capabilities",
                *capability_lines,
                "",
                "## LLM",
                "```yaml",
                yaml.safe_dump(spec.llm, allow_unicode=True, sort_keys=False).strip() or "{}",
                "```",
            ]
        )
        self._write_page(
            group="agents",
            page_name=_slugify(agent_name),
            page_type="agent",
            tags=["agent", "system"],
            sources=[spec.source_path] if spec.source_path else [],
            body=body,
        )

    def _write_system_inventory_page(self, system_paths: list[Path]) -> None:
        rows = [
            "# System Inventory",
            "",
            "## Coverage",
            f"- scanned files: {len(system_paths)}",
            f"- skills: {len(self.registry.skills)}",
            f"- agents: {len(self.registry.agent_specs)}",
            f"- toolboxes: {len(self.registry.toolboxes)}",
            "",
            "## Key Files",
        ]
        for path in system_paths[:200]:
            rows.append(f"- `[[raw/system/{self._raw_system_name(path)}]]`")
        self._write_page(
            group="system",
            page_name="inventory",
            page_type="system",
            tags=["system", "inventory"],
            sources=["registry.iter_system_source_files"],
            body="\n".join(rows),
        )

    def _ingest_business_file(self, skill_id: str, source_path: Path) -> None:
        raw_target = self.raw_root / "business" / _slugify(skill_id) / source_path.name
        _copy_text_or_note(source_path, raw_target)
        text = raw_target.read_text(encoding="utf-8")
        body = "\n".join(
            [
                f"# {source_path.name}",
                "",
                f"- owner_skill: `[[技能/{_slugify(skill_id)}]]`",
                f"- raw: `[[raw/business/{_slugify(skill_id)}/{source_path.name}]]`",
                "",
                "## Summary",
                _first_paragraph(text, 800) or "(empty)",
                "",
                "## Content",
                text[:6000] if text else "(empty)",
            ]
        )
        self._write_page(
            group="sources",
            page_name=_slugify(skill_id + "__" + source_path.stem),
            page_type="source",
            tags=["business", "source"],
            sources=[str(source_path.relative_to(self.project_root).as_posix())],
            body=body,
        )

    def _write_attachment_page(self, meta: dict[str, Any]) -> None:
        summary = meta.get("summary") or meta.get("status") or "no summary"
        raw_link = meta.get("raw_link") or "(not stored)"
        body = "\n".join(
            [
                f"# {meta['name']}",
                "",
                f"- source_url: `{meta['url']}`",
                f"- stored: `{meta.get('stored_path', '(none)')}`",
                f"- raw: `{raw_link}`",
                f"- status: `{meta['status']}`",
                "",
                "## Summary",
                summary,
                "",
                "## Snippet",
                meta.get("snippet", "(not parsed)"),
            ]
        )
        self._write_page(
            group="attachments",
            page_name=_slugify(meta["name"]),
            page_type="attachment",
            tags=["attachment", "user"],
            sources=[meta["url"]],
            body=body,
        )

    def _persist_user_source(self, *, name: str, url: str) -> dict[str, Any]:
        convo_dir = self.raw_root / "users" / _slugify(self.session.settings.conversation_id)
        convo_dir.mkdir(parents=True, exist_ok=True)
        target = convo_dir / name
        status = "stored"
        snippet = "(not parsed)"
        summary = ""
        raw_link = None
        parsed = urlparse(url)

        try:
            if parsed.scheme in {"http", "https"}:
                response = requests.get(url, timeout=20)
                response.raise_for_status()
                target.write_bytes(response.content)
            else:
                local_path = Path(url.replace("file://", "")).expanduser().resolve()
                if local_path.exists():
                    shutil.copy2(local_path, target)
                else:
                    status = "metadata_only"
            if target.exists() and target.suffix.lower() in {".md", ".txt", ".py", ".json", ".yaml", ".yml", ".csv", ".toml"}:
                text = target.read_text(encoding="utf-8")
                snippet = text[:4000] if text else "(empty)"
                summary = _first_paragraph(text, 600)
                raw_link = f"[[raw/users/{_slugify(self.session.settings.conversation_id)}/{name}]]"
            elif target.exists():
                raw_link = f"[[raw/users/{_slugify(self.session.settings.conversation_id)}/{name}]]"
                summary = f"Attachment stored but not parsed as text due to extension: {target.suffix or '(none)'}"
            else:
                summary = "Attachment metadata recorded, but content was not fetched."
        except Exception as exc:  # noqa: BLE001
            status = f"error:{exc.__class__.__name__}"
            summary = f"Failed to ingest attachment content: {exc}"

        return {
            "name": name,
            "url": url,
            "status": status,
            "stored_path": str(target) if target.exists() else "",
            "summary": summary,
            "snippet": snippet,
            "raw_link": raw_link,
        }

    def _mirror_system_raw(self, source_path: Path) -> None:
        if source_path is None:
            return
        raw_target = self.raw_root / "system" / self._raw_system_name(source_path)
        _copy_text_or_note(source_path, raw_target)

    def _raw_system_name(self, source_path: Path | None) -> str:
        if source_path is None:
            return "unknown.txt"
        rel = source_path.resolve().relative_to(self.project_root.resolve())
        return _slugify(str(rel)) + source_path.suffix

    def _sync_index(self) -> None:
        groups = {key: list((self.wiki_root / dirname).glob("*.md")) for key, dirname in WIKI_GROUPS.items()}
        lines = ["# Wiki Index", "", f"- last_updated: {_utc_now()}"]
        for key, dirname in WIKI_GROUPS.items():
            pages = sorted(groups[key])
            lines.append(f"- {dirname}: {len(pages)}")
        lines.extend(["", "## Pages"])
        for key, dirname in WIKI_GROUPS.items():
            lines.append(f"### {dirname}")
            pages = sorted(groups[key])
            if not pages:
                lines.append("- (empty)")
                continue
            for page in pages:
                title = _titleize(page)
                lines.append(f"- [[{self._relative_page_path(page)}]] · {title}")
            lines.append("")
        self.index_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    def _search_hits(self, *, query: str, limit: int = 10, groups: list[str] | None = None) -> list[SearchHit]:
        tokens = [token for token in re.split(r"\W+", query.lower()) if token]
        if not tokens:
            return []
        pages = list(self._iter_wiki_pages(groups=groups))
        hits: list[SearchHit] = []
        for page in pages:
            text = page.read_text(encoding="utf-8")
            lowered = text.lower()
            rel = self._relative_page_path(page)
            score = 0
            for token in tokens:
                score += lowered.count(token)
                score += rel.lower().count(token) * 3
            if score <= 0:
                continue
            _, body = _split_frontmatter(text)
            hits.append(
                SearchHit(
                    path=rel,
                    title=_titleize(page),
                    score=score,
                    preview=_first_paragraph(body, 220),
                )
            )
        hits.sort(key=lambda item: (-item.score, item.path))
        return hits[:limit]

    def _iter_wiki_pages(self, groups: list[str] | None = None):
        if groups:
            for group in groups:
                dirname = WIKI_GROUPS.get(group, group)
                yield from sorted((self.wiki_root / dirname).glob("*.md"))
            return
        for dirname in WIKI_GROUPS.values():
            yield from sorted((self.wiki_root / dirname).glob("*.md"))

    def _resolve_page(self, page: str) -> Path:
        candidate = (self.wiki_root / page).resolve()
        if candidate.exists() and candidate.is_file():
            return candidate
        for file in self._iter_wiki_pages():
            if self._relative_page_path(file) == page:
                return file
            if file.stem == page or _titleize(file) == page:
                return file
        raise FileNotFoundError(page)

    def _relative_page_path(self, page: Path) -> str:
        return str(page.relative_to(self.wiki_root).as_posix())

    def _normalize_link_target(self, link: str) -> str:
        text = link.strip()
        if text.endswith(".md"):
            return text
        if "/" in text:
            return text + ".md"
        for dirname in WIKI_GROUPS.values():
            candidate = f"{dirname}/{text}.md"
            target = self.wiki_root / candidate
            if target.exists():
                return candidate
        return text + ".md"

    def _write_page(
        self,
        *,
        group: str,
        page_name: str,
        page_type: str,
        tags: list[str],
        sources: list[str],
        body: str,
    ) -> Path:
        dirname = WIKI_GROUPS[group]
        path = self.wiki_root / dirname / f"{page_name}.md"
        frontmatter = {
            "type": page_type,
            "tags": tags,
            "sources": sources,
            "created": _utc_today(),
            "updated": _utc_today(),
        }
        if path.exists():
            meta, _ = _split_frontmatter(path.read_text(encoding="utf-8"))
            frontmatter["created"] = meta.get("created", frontmatter["created"])
        text = "---\n" + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip() + "\n---\n\n" + body.strip() + "\n"
        path.write_text(text, encoding="utf-8")
        return path

    def _append_log(self, action: str, title: str, payload: dict[str, Any]) -> None:
        block = [
            f"## [{_utc_today()}] {action} | {title}",
            "",
            f"- payload: `{json.dumps(payload, ensure_ascii=False, sort_keys=True)}`",
            "",
        ]
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write("\n".join(block))

    def _module_to_path(self, module_name: str) -> Path | None:
        if not module_name.startswith(("tools.", "runtime.", "governance.", "context.", "agents.", "skills.")):
            return None
        candidate = self.project_root / "src" / Path(*module_name.split("."))
        file_candidate = candidate.with_suffix(".py")
        if file_candidate.exists():
            return file_candidate
        return None

    def _read_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
