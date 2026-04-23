from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from governance.protocol_index import ProtocolIndexer, extract_markdown_links


LEGACY_PATTERNS = (
    "_knowledge" + "_hubs",
    "data/" + "wiki",
    "wiki" + ".refresh",
    "wiki" + ".ingest_files",
)

ACTION_LINE_RE = re.compile(r"^[-*]\s+`?([a-z][a-z0-9_]*\.[a-z0-9_]+)`?\s*$")


@dataclass(slots=True)
class RepositoryLint:
    project_root: Path
    issues: list[dict[str, Any]] = field(default_factory=list)

    def run(self) -> dict[str, Any]:
        indexer = ProtocolIndexer(self.project_root)
        result = indexer.scan()
        resolvable = set(result.entities) | set(result.pages)

        self._check_single_markdown_rule()
        self._check_links(resolvable)
        self._check_legacy_paths()
        self._check_forbidden_other()
        self._check_skill_tool_links(result.entities)
        self._check_agent_runtime_sections(result.entities)
        self._check_tool_implementation_sections(result.entities)
        self._check_tool_page_protocol_noise(result.entities)

        return {
            "status": "ok" if not self.issues else "error",
            "issue_count": len(self.issues),
            "issues": self.issues,
        }

    def _check_single_markdown_rule(self) -> None:
        src_root = self.project_root / "src"
        for folder in sorted(src_root.rglob("*")):
            if not folder.is_dir() or "__pycache__" in folder.parts:
                continue
            markdowns = [path.name for path in folder.iterdir() if path.is_file() and path.suffix.lower() == ".md"]
            if len(markdowns) > 1:
                self.issues.append(
                    {
                        "rule": "single_md_per_folder",
                        "folder": str(folder.relative_to(self.project_root).as_posix()),
                        "markdowns": sorted(markdowns),
                    }
                )

    def _check_links(self, resolvable: set[str]) -> None:
        src_root = self.project_root / "src"
        for path in sorted(src_root.rglob("*.md")):
            if "__pycache__" in path.parts:
                continue
            for link in extract_markdown_links(path.read_text(encoding="utf-8")):
                if link in resolvable:
                    continue
                rule = "page_link_resolves" if link.startswith("page/") else "entity_link_resolves"
                self.issues.append(
                    {
                        "rule": rule,
                        "path": str(path.relative_to(self.project_root).as_posix()),
                        "target": link,
                    }
                )

    def _check_legacy_paths(self) -> None:
        for path in sorted(self.project_root.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".pyc"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for pattern in LEGACY_PATTERNS:
                if pattern in text:
                    self.issues.append(
                        {
                            "rule": "no_legacy_strings",
                            "path": str(path.relative_to(self.project_root).as_posix()),
                            "pattern": pattern,
                        }
                    )

    def _check_forbidden_other(self) -> None:
        other_path = self.project_root / "src" / "other"
        if other_path.exists():
            self.issues.append(
                {
                    "rule": "no_src_other",
                    "path": str(other_path.relative_to(self.project_root).as_posix()),
                }
            )

    def _check_skill_tool_links(self, entities: dict[str, Any]) -> None:
        for node_id, node in sorted(entities.items()):
            if node.kind != "skill":
                continue
            path = self.project_root / node.path
            text = path.read_text(encoding="utf-8")
            if "actions" in node.section_map:
                self.issues.append(
                    {
                        "rule": "skill_uses_tool_links",
                        "path": node.path,
                        "section": "actions",
                    }
                )
                continue
            for line in text.splitlines():
                match = ACTION_LINE_RE.match(line.strip())
                if not match:
                    continue
                action_id = match.group(1)
                expected_link = f"[[tool/{action_id.replace('.', '/')}]]"
                if expected_link not in text:
                    self.issues.append(
                        {
                            "rule": "skill_uses_tool_links",
                            "path": node.path,
                            "action_id": action_id,
                        }
                    )

    def _check_agent_runtime_sections(self, entities: dict[str, Any]) -> None:
        banned_markers = ("## LLM", "## Context Policy", "provider=", "model=", "max_prompt_chars=")
        for node in entities.values():
            if node.kind != "agent":
                continue
            text = (self.project_root / node.path).read_text(encoding="utf-8")
            violations = [marker for marker in banned_markers if marker in text]
            if violations:
                self.issues.append(
                    {
                        "rule": "agent_runtime_config_not_in_page",
                        "path": node.path,
                        "markers": violations,
                    }
                )

    def _check_tool_implementation_sections(self, entities: dict[str, Any]) -> None:
        for node in entities.values():
            if node.kind != "tool":
                continue
            if "implementation" not in node.section_map:
                continue
            items = node.code_items.get("implementation", [])
            if items == ["impl.py"] and "impl.py" in node.truth_ext:
                continue
            self.issues.append(
                {
                    "rule": "tool_impl_is_adjacent_impl_py",
                    "path": node.path,
                    "implementation_items": items,
                    "truth_ext": node.truth_ext,
                }
            )

    def _check_tool_page_protocol_noise(self, entities: dict[str, Any]) -> None:
        banned_markers = ("Canonical tool page", "## Action ID")
        for node in entities.values():
            if node.kind != "tool":
                continue
            text = (self.project_root / node.path).read_text(encoding="utf-8")
            violations = [marker for marker in banned_markers if marker in text]
            if violations:
                self.issues.append(
                    {
                        "rule": "tool_page_not_protocolized",
                        "path": node.path,
                        "markers": violations,
                    }
                )


def lint_repository(project_root: Path) -> str:
    payload = RepositoryLint(Path(project_root).resolve()).run()
    return json.dumps(payload, ensure_ascii=False, indent=2)
