from __future__ import annotations

from pathlib import Path

from schemas.agent import AgentSpec
from schemas.skill import SkillSpec
from shared.errors import RegistryError
from tool.indexes.toolbox_registry import ToolboxRegistry

from governance.protocol_index import ProtocolIndexer, tool_link_to_action_id
from governance.refs import RefResolver


TEXT_EXTENSIONS = {".md", ".markdown", ".txt", ".yaml", ".yml", ".json", ".csv", ".py", ".toml", ".cfg", ".env"}

LLM_SETTING_KEYS = {"provider", "model", "api_key", "base_url"}


class SpecRegistry:
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.src_root = self.project_root / "src"
        self.skills_root = self.src_root / "skill"
        self.agents_root = self.src_root / "agent"
        self.context_root = self.src_root / "context"
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
        self.refs_resolver = RefResolver(self.skills)

    def _scan_skills(self) -> dict[str, SkillSpec]:
        skills: dict[str, SkillSpec] = {}
        if not self.skills_root.exists():
            raise RegistryError(f"Skills root not found: {self.skills_root}")
        for skill_id, node in sorted(self.protocol.entities.items()):
            if not skill_id.startswith("skill/"):
                continue
            markdown = self.project_root / node.path
            skills[skill_id] = SkillSpec(
                skill_id=skill_id,
                name=node.title,
                description=node.summary,
                directory=markdown.parent,
                markdown_path=markdown,
                markdown_body=markdown.read_text(encoding="utf-8"),
                frontmatter={},
                children=self._links_from_node(node, {"child skills"}, prefix="skill/"),
                refs=self._links_from_node(node, {"refs"}, prefix="skill/"),
                actions=self._actions_from_node(node),
                tags=[],
                knowledge_files=self._collect_knowledge_files(markdown.parent),
            )
        return skills

    def _scan_agent_specs(self) -> dict[str, AgentSpec]:
        specs: dict[str, AgentSpec] = {}
        for agent_id, node in sorted(self.protocol.entities.items()):
            if not agent_id.startswith("agent/"):
                continue
            root_skill_links = self._links_from_node(node, {"root skill"}, prefix="skill/")
            if not root_skill_links:
                raise RegistryError(f"Agent page is missing a root skill link: {node.path}")

            llm = self._mapping_from_settings(node.settings, include_keys=LLM_SETTING_KEYS)
            context_policy = self._mapping_from_settings(node.settings, exclude_keys=LLM_SETTING_KEYS)
            if not llm:
                llm = self._mapping_from_items(self._code_items_from_node(node, "llm"))
            if not context_policy:
                context_policy = self._mapping_from_items(self._code_items_from_node(node, "context policy"))

            spec = AgentSpec(
                name=agent_id.rsplit("/", 1)[-1],
                root_skill=root_skill_links[0],
                description=node.summary,
                toolboxes=self._code_items_from_node(node, "toolboxes"),
                capabilities=self._code_items_from_node(node, "capabilities"),
                llm=llm,
                context_policy=context_policy,
                source_path=node.path,
            )
            specs[spec.name] = spec
        return specs

    def _scan_context_assets(self) -> dict[str, Path]:
        assets: dict[str, Path] = {}
        mappings = {
            "system_prompt.md": self.context_root / "system" / "default" / "template.txt",
            "tool_result.md": self.context_root / "tool_result" / "default" / "template.txt",
            "compact_summary.md": self.context_root / "compact_summary" / "default" / "template.txt",
        }
        for name, path in mappings.items():
            if path.exists():
                assets[name] = path
        return assets

    def _collect_knowledge_files(self, directory: Path) -> list[Path]:
        knowledge_dir = directory / "knowledge"
        if not knowledge_dir.exists():
            return []
        rows: list[Path] = []
        for path in sorted(knowledge_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS:
                rows.append(path)
        return rows

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
            self.context_root,
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
    def _links_from_node(node, titles: set[str], *, prefix: str | None = None) -> list[str]:  # noqa: ANN001
        rows: list[str] = []
        for title in titles:
            for link in node.section_links.get(title, []):
                if prefix and not link.startswith(prefix):
                    continue
                rows.append(link)
        return SpecRegistry._ordered_unique(rows)

    @staticmethod
    def _code_items_from_node(node, *titles: str) -> list[str]:  # noqa: ANN001
        rows: list[str] = []
        for title in titles:
            rows.extend(node.code_items.get(title, []))
        return SpecRegistry._ordered_unique(rows)

    def _actions_from_node(self, node) -> list[str]:  # noqa: ANN001
        tool_links = self._links_from_node(node, {"tools"}, prefix="tool/")
        rows = [tool_link_to_action_id(link) for link in tool_links]
        rows.extend(self._code_items_from_node(node, "actions"))
        return self._ordered_unique(rows)

    @staticmethod
    def _mapping_from_items(items: list[str]) -> dict[str, int | str]:
        payload: dict[str, int | str] = {}
        for item in items:
            if "=" not in item:
                continue
            key, value = item.split("=", 1)
            cleaned_key = key.strip().strip("`")
            cleaned_value = value.strip().strip("`")
            if not cleaned_key:
                continue
            payload[cleaned_key] = int(cleaned_value) if cleaned_value.isdigit() else cleaned_value
        return payload

    @staticmethod
    def _mapping_from_settings(
        settings: dict[str, str],
        *,
        include_keys: set[str] | None = None,
        exclude_keys: set[str] | None = None,
    ) -> dict[str, int | str]:
        payload: dict[str, int | str] = {}
        for key, value in settings.items():
            if include_keys is not None and key not in include_keys:
                continue
            if exclude_keys is not None and key in exclude_keys:
                continue
            payload[key] = int(value) if value.isdigit() else value
        return payload

    @staticmethod
    def _ordered_unique(rows: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for item in rows:
            if item in seen:
                continue
            seen.add(item)
            ordered.append(item)
        return ordered
