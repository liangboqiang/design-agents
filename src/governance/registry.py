from __future__ import annotations

from pathlib import Path

import yaml

from schemas.agent import AgentSpec
from schemas.skill import SkillSpec
from shared.errors import RegistryError
from tools.indexes.toolbox_registry import ToolboxRegistry

from .refs_resolver import RefsResolver


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


class GovernanceRegistry:
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.src_root = self.project_root / "src"
        self.skills_root = self.src_root / "skills"
        self.agents_root = self.src_root / "agents"
        self.context_root = self.src_root / "context"
        self.toolbox_registry = ToolboxRegistry()

        self.skills: dict[str, SkillSpec] = {}
        self.agent_specs: dict[str, AgentSpec] = {}
        self.context_assets: dict[str, Path] = {}
        self.toolboxes = self.toolbox_registry.discover()
        self.refresh()

    def refresh(self) -> None:
        self.skills = self._scan_skills()
        self.agent_specs = self._scan_agent_specs()
        self.context_assets = self._scan_context_assets()
        self.refs_resolver = RefsResolver(self.skills)

    def _scan_skills(self) -> dict[str, SkillSpec]:
        skills: dict[str, SkillSpec] = {}
        if not self.skills_root.exists():
            raise RegistryError(f"Skills root not found: {self.skills_root}")
        for markdown in sorted(self.skills_root.rglob("SKILL.md")):
            meta, body = _split_frontmatter(markdown.read_text(encoding="utf-8"))
            skill_id = self._skill_id_for(markdown.parent)
            skills[skill_id] = SkillSpec(
                skill_id=skill_id,
                name=str(meta.get("name", markdown.parent.name)),
                description=str(meta.get("description") or "").strip(),
                directory=markdown.parent,
                markdown_path=markdown,
                markdown_body=body,
                frontmatter=meta,
                children=list(meta.get("children") or []),
                refs=list(meta.get("refs") or []),
                actions=[str(item) for item in meta.get("actions") or []],
                tags=[str(item) for item in meta.get("tags") or []],
            )
        for skill in skills.values():
            skill.children = [self._normalize_ref(skill.directory, ref) for ref in skill.children]
            skill.refs = [self._normalize_ref(skill.directory, ref) for ref in skill.refs]
        return skills

    def _skill_id_for(self, directory: Path) -> str:
        try:
            rel = directory.resolve().relative_to(self.skills_root)
        except ValueError as exc:
            raise RegistryError(
                f"Skill reference escaped skills root: {directory.resolve()} is outside {self.skills_root}"
            ) from exc
        return str(rel).replace("\\", "/")

    def _normalize_ref(self, owner_directory: Path, ref: str) -> str:
        ref_path = (owner_directory / ref).resolve()
        if ref_path.is_file():
            ref_path = ref_path.parent
        return self._skill_id_for(ref_path)

    def _scan_agent_specs(self) -> dict[str, AgentSpec]:
        specs: dict[str, AgentSpec] = {}
        specs_dir = self.agents_root / "specs"
        if not specs_dir.exists():
            return specs
        for spec_path in sorted(specs_dir.glob("*.agent.yaml")):
            payload = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
            spec = AgentSpec.from_mapping(payload)
            specs[spec.name] = spec
        return specs

    def _scan_context_assets(self) -> dict[str, Path]:
        assets: dict[str, Path] = {}
        for path in sorted((self.context_root / "templates").glob("*")):
            assets[path.name] = path
        return assets

    def get_skill(self, skill_id: str) -> SkillSpec:
        return self.skills[skill_id]

    def list_children_cards(self, skill_id: str) -> list[tuple[str, str]]:
        skill = self.get_skill(skill_id)
        rows: list[tuple[str, str]] = []
        for child_id in skill.children:
            child = self.get_skill(child_id)
            rows.append((child_id, child.description or child.name))
        return rows

    def get_agent_spec(self, agent_name: str) -> AgentSpec:
        return self.agent_specs[agent_name]
