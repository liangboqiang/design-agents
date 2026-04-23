from __future__ import annotations

import json
from pathlib import Path

from schemas.agent import AgentSpec
from schemas.skill import SkillSpec
from shared.errors import RegistryError
from tool.indexes.toolbox_registry import ToolboxRegistry

from .protocol_index import (
    ProtocolIndexer,
    extract_markdown_links,
    extract_markdown_title,
    extract_section_code_items,
    first_paragraph,
    split_markdown_sections,
)
from .refs_resolver import RefsResolver


TEXT_EXTENSIONS = {".md", ".markdown", ".txt", ".yaml", ".yml", ".json", ".csv", ".py", ".toml"}


class GovernanceRegistry:
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.src_root = self.project_root / "src"
        self.skills_root = self.src_root / "skill"
        self.agents_root = self.src_root / "agent"
        self.ctx_root = self.src_root / "ctx"
        self.context_root = self.ctx_root
        self.tools_root = self.src_root / "tool"
        self.toolbox_registry = ToolboxRegistry()

        self.skills: dict[str, SkillSpec] = {}
        self.agent_specs: dict[str, AgentSpec] = {}
        self.context_assets: dict[str, Path] = {}
        self.protocol = None
        self.toolboxes = self.toolbox_registry.discover()
        self.refresh()

    def refresh(self) -> None:
        self.protocol = ProtocolIndexer(self.project_root).scan()
        self.skills = self._scan_skills()
        self.agent_specs = self._scan_agent_specs()
        self.context_assets = self._scan_context_assets()
        self.refs_resolver = RefsResolver(self.skills)

    def _scan_skills(self) -> dict[str, SkillSpec]:
        skills: dict[str, SkillSpec] = {}
        if not self.skills_root.exists():
            raise RegistryError(f"Skills root not found: {self.skills_root}")
        for skill_id, node in sorted(self.protocol.entities.items()):
            if not skill_id.startswith("skill/"):
                continue
            markdown = self.project_root / node.path
            text = markdown.read_text(encoding="utf-8")
            sections = split_markdown_sections(text)
            children = self._links_from_sections(
                sections,
                {"子技能", "Child Skills", "Children"},
                prefix="skill/",
            )
            refs = self._links_from_sections(
                sections,
                {"引用", "相关内容", "Refs", "Related"},
                prefix="skill/",
            )
            actions = self._actions_from_sections(sections)
            skills[skill_id] = SkillSpec(
                skill_id=skill_id,
                name=extract_markdown_title(text, markdown.parent.name),
                description=first_paragraph(text),
                directory=markdown.parent,
                markdown_path=markdown,
                markdown_body=text,
                frontmatter={},
                children=children,
                refs=refs,
                actions=actions,
                tags=[],
                knowledge_files=self._collect_knowledge_files(markdown.parent),
            )
        return skills

    def _collect_knowledge_files(self, directory: Path) -> list[Path]:
        knowledge_dir = directory / "knowledge"
        if not knowledge_dir.exists():
            return []
        rows: list[Path] = []
        for path in sorted(knowledge_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS:
                rows.append(path)
        return rows

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
        for agent_id, node in sorted(self.protocol.entities.items()):
            if not agent_id.startswith("agent/"):
                continue
            markdown = self.project_root / node.path
            text = markdown.read_text(encoding="utf-8")
            sections = split_markdown_sections(text)
            root_skill_links = self._links_from_sections(sections, {"根技能", "Root Skill"}, prefix="skill/")
            if not root_skill_links:
                raise RegistryError(f"Agent page is missing a root skill link: {markdown}")
            spec = AgentSpec(
                name=agent_id.rsplit("/", 1)[-1],
                root_skill=root_skill_links[0],
                description=first_paragraph(text),
                toolboxes=self._section_code_items(sections, "工具箱", "Toolboxes"),
                capabilities=self._section_code_items(sections, "能力", "Capabilities"),
                llm=self._llm_from_section(sections.get("LLM", "")),
                context_policy=self._context_policy_from_section(
                    sections.get("上下文策略", "") or sections.get("Context Policy", "")
                ),
                source_path=str(markdown.relative_to(self.project_root).as_posix()),
            )
            specs[spec.name] = spec
        return specs

    def _scan_context_assets(self) -> dict[str, Path]:
        assets: dict[str, Path] = {}
        mappings = {
            "system_prompt.md": self.ctx_root / "system" / "default" / "template.txt",
            "tool_result.md": self.ctx_root / "tool_result" / "default" / "template.txt",
            "compact_summary.md": self.ctx_root / "compact_summary" / "default" / "template.txt",
        }
        for name, path in mappings.items():
            if path.exists():
                assets[name] = path
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

    def iter_business_source_files(self) -> list[Path]:
        rows: list[Path] = []
        for skill in self.skills.values():
            rows.extend(skill.knowledge_files)
        return sorted({path.resolve() for path in rows})

    def iter_system_source_files(self) -> list[Path]:
        rows: list[Path] = []
        include_roots = [
            self.skills_root,
            self.agents_root,
            self.ctx_root,
            self.tools_root,
            self.src_root / "runtime",
            self.src_root / "governance",
            self.src_root / "wiki",
            self.src_root / "domain",
        ]
        for base in include_roots:
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if not path.is_file():
                    continue
                if path.name.startswith("."):
                    continue
                if "__pycache__" in path.parts:
                    continue
                if path.suffix.lower() not in TEXT_EXTENSIONS:
                    continue
                rows.append(path.resolve())
        return sorted(set(rows))

    @staticmethod
    def _links_from_sections(sections: dict[str, str], titles: set[str], *, prefix: str | None = None) -> list[str]:
        rows: list[str] = []
        for title in titles:
            for link in extract_markdown_links(sections.get(title, "")):
                if prefix and not link.startswith(prefix):
                    continue
                rows.append(link)
        seen: set[str] = set()
        ordered: list[str] = []
        for item in rows:
            if item in seen:
                continue
            seen.add(item)
            ordered.append(item)
        return ordered

    def _actions_from_sections(self, sections: dict[str, str]) -> list[str]:
        rows: list[str] = []
        for title in ("动作", "Actions", "使用动作", "入口动作"):
            rows.extend(extract_section_code_items(sections.get(title, "")))
        if rows:
            return rows
        tool_links = self._links_from_sections(
            sections,
            {"入口工具", "使用工具", "Tools", "相关内容"},
            prefix="tool/",
        )
        return [self._tool_link_to_action_id(link) for link in tool_links]

    @staticmethod
    def _tool_link_to_action_id(link: str) -> str:
        parts = link.split("/")
        if len(parts) < 3:
            return link.replace("/", ".")
        return ".".join(parts[1:])

    @staticmethod
    def _llm_from_section(section: str) -> dict[str, str]:
        payload: dict[str, str] = {}
        for line in section.splitlines():
            stripped = line.strip().lstrip("- ").strip()
            if "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            payload[key.strip().strip("`")] = value.strip().strip("`")
        return payload

    @staticmethod
    def _context_policy_from_section(section: str) -> dict[str, int | str]:
        payload: dict[str, int | str] = {}
        for line in section.splitlines():
            stripped = line.strip().lstrip("- ").strip()
            if "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            value = value.strip().strip("`")
            if value.isdigit():
                payload[key.strip().strip("`")] = int(value)
            else:
                payload[key.strip().strip("`")] = value
        return payload

    @staticmethod
    def _section_code_items(sections: dict[str, str], *titles: str) -> list[str]:
        for title in titles:
            text = sections.get(title, "")
            if text:
                return extract_section_code_items(text)
        return []
