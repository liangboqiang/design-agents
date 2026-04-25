from __future__ import annotations

from pathlib import Path
from typing import Any

from .compiler import ProtocolCompiler
from .types import AgentSpec, ProtocolView, SkillSpec, ToolSpec, ToolboxSpec


class RuntimeRegistry:
    """Runtime facade over ProtocolView.

    The registry does not scan files directly. It consumes the hard ProtocolView
    compiled from the unified Wiki Hub.
    """

    def __init__(self, view: ProtocolView, *, project_root: Path, toolbox_classes: dict[str, type[Any]] | None = None):
        self.view = view
        self.project_root = Path(project_root).resolve()
        self.toolbox_classes = dict(toolbox_classes or {})

    @classmethod
    def from_wiki(cls, project_root: Path) -> "RuntimeRegistry":
        compiler = ProtocolCompiler.from_wiki(project_root)
        view = compiler.compile()
        return cls(view, project_root=project_root, toolbox_classes=compiler.toolbox_classes)

    @property
    def agents(self) -> dict[str, AgentSpec]:
        return self.view.agents

    @property
    def skills(self) -> dict[str, SkillSpec]:
        return self.view.skills

    @property
    def tools(self) -> dict[str, ToolSpec]:
        return self.view.tools

    @property
    def toolboxes(self) -> dict[str, ToolboxSpec]:
        return self.view.toolboxes

    def agent(self, agent_id: str) -> AgentSpec:
        return self.view.agents[agent_id]

    def get_agent_spec(self, agent_id: str) -> AgentSpec:
        return self.agent(agent_id)

    def skill(self, skill_id: str) -> SkillSpec:
        return self.view.skills[skill_id]

    def get_skill(self, skill_id: str) -> SkillSpec:
        return self.skill(skill_id)

    def tool(self, tool_id: str) -> ToolSpec:
        return self.view.tools[tool_id]

    def toolbox(self, toolbox_id: str) -> ToolboxSpec:
        return self.view.toolboxes[toolbox_id]

    def children(self, skill_id: str) -> list[SkillSpec]:
        return [self.view.skills[item] for item in self.view.skills[skill_id].child_skills if item in self.view.skills]

    def refs(self, skill_id: str) -> list[SkillSpec]:
        seen: set[str] = set()
        ordered: list[SkillSpec] = []

        def visit(current: str) -> None:
            if current in seen or current not in self.view.skills:
                return
            seen.add(current)
            skill = self.view.skills[current]
            ordered.append(skill)
            for ref in skill.refs:
                visit(ref)

        visit(skill_id)
        return ordered

    def base_skill_ids(self, skill_id: str) -> list[str]:
        return [skill.skill_id for skill in self.refs(skill_id)]

    def list_children_cards(self, skill_id: str) -> list[tuple[str, str]]:
        return [(skill.skill_id, skill.summary or skill.title) for skill in self.children(skill_id)]

    def create_toolbox(self, toolbox_id: str, workspace_root: Path):
        cls = self.toolbox_classes[toolbox_id]
        return cls().spawn(workspace_root)

    def diagnostics_report(self) -> str:
        if not self.view.diagnostics:
            return "Protocol diagnostics: clean."
        return "\\n".join(f"[{d.level}] {d.node_id}: {d.message}" for d in self.view.diagnostics)
