from __future__ import annotations

from pathlib import Path

import yaml

from .models import SkillNode


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


class SkillCatalog:
    def __init__(self, root_directory: Path):
        self.root_directory = root_directory.resolve()
        self.skills: dict[str, SkillNode] = {}
        self._load()

    def _load(self) -> None:
        for md in sorted(self.root_directory.rglob("SKILL.md")):
            meta, body = _split_frontmatter(md.read_text(encoding="utf-8"))
            skill_id = self._skill_id_for(md.parent)
            self.skills[skill_id] = SkillNode(
                skill_id=skill_id,
                name=meta.get("name", md.parent.name),
                description=(meta.get("description") or "").strip(),
                directory=md.parent,
                markdown_path=md,
                markdown_body=body,
                frontmatter=meta,
                children=list(meta.get("children") or []),
                refs=list(meta.get("refs") or []),
                actions=[str(item) for item in list(meta.get("actions") or [])],
            )
        self._resolve_relative_links()

    def _skill_id_for(self, directory: Path) -> str:
        rel = directory.resolve().relative_to(self.root_directory)
        text = str(rel).replace("\\", "/")
        return "root" if text == "." else text

    def _normalize_ref(self, owner: SkillNode, ref: str) -> str:
        ref_path = (owner.directory / ref).resolve()
        if ref_path.is_file():
            ref_path = ref_path.parent
        return self._skill_id_for(ref_path)

    def _resolve_relative_links(self) -> None:
        for node in self.skills.values():
            node.children = [self._normalize_ref(node, ref) for ref in node.children]
            node.refs = [self._normalize_ref(node, ref) for ref in node.refs]

    def get(self, skill_id: str) -> SkillNode:
        return self.skills[skill_id]

    def closure_for_active_skill(self, skill_id: str) -> list[str]:
        node = self.get(skill_id)
        return [skill_id, *node.refs]

    def list_children_cards(self, skill_id: str) -> list[tuple[str, str]]:
        node = self.get(skill_id)
        return [(child, self.get(child).description or self.get(child).name) for child in node.children]
