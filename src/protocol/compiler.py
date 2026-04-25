from __future__ import annotations

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Any

from wiki.adapter_bridge import WikiAdapterBridge
from .adapter import ProtocolAdapter, NormalizedNode
from .types import (
    AgentSpec,
    ProtocolDiagnostic,
    ProtocolGraph,
    ProtocolView,
    SkillSpec,
    ToolSpec,
    ToolboxSpec,
)


TOOL_PACKAGES = ("tool.external", "tool.workflow", "tool.system")


def is_toolbox_class(module_name: str, obj: object) -> bool:
    return (
        inspect.isclass(obj)
        and obj.__module__ == module_name
        and bool(getattr(obj, "toolbox_name", ""))
        and callable(getattr(obj, "tool_specs", None))
        and callable(getattr(obj, "spawn", None))
    )


class ProtocolCompiler:
    """Compile Wiki Nodes into hard ProtocolView consumed by Runtime."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.adapter = ProtocolAdapter()
        self.toolbox_classes: dict[str, type[Any]] = {}

    @classmethod
    def from_wiki(cls, project_root: Path) -> "ProtocolCompiler":
        return cls(project_root)

    def compile(self) -> ProtocolView:
        nodes = WikiAdapterBridge(self.project_root).iter_nodes()
        normalized = [self.adapter.normalize(node) for node in nodes]
        view = ProtocolView()
        for item in normalized:
            view.diagnostics.extend(item.diagnostics)
            if item.node_type == "agent":
                self._add_agent(view, item)
            elif item.node_type == "skill":
                self._add_skill(view, item)
            elif item.node_type == "toolbox":
                self._add_toolbox(view, item)
            elif item.node_type == "tool":
                self._add_tool(view, item)

        self._discover_python_toolboxes(view)
        self._validate(view)
        self._build_graph(view, normalized)
        return view

    def _add_agent(self, view: ProtocolView, item: NormalizedNode) -> None:
        policy = dict(item.fields.get("policy") or {})
        policy.update(self._read_agent_runtime_file(item))
        agent_id = item.node_id.rsplit("/", 1)[-1] if item.node_id.startswith("agent/") else item.node_id
        view.agents[agent_id] = AgentSpec(
            agent_id=agent_id,
            title=str(item.fields.get("title") or agent_id),
            root_skill=str(item.fields.get("root_skill") or ""),
            toolboxes=list(item.fields.get("toolboxes") or []),
            context=str(item.fields.get("context") or ""),
            llm={key: policy.pop(key) for key in list(policy.keys()) if key in {"provider", "model", "api_key", "base_url"}},
            policy=policy,
            source_node=item.node.node_id,
        )

    def _read_agent_runtime_file(self, item: NormalizedNode) -> dict[str, object]:
        source_path = self.project_root / str(item.fields.get("source_path") or "")
        runtime_file = source_path.parent / "runtime.toml"
        if not runtime_file.exists():
            return {}
        try:
            import tomllib
            return dict(tomllib.loads(runtime_file.read_text(encoding="utf-8")))
        except Exception:
            return {}

    def _add_skill(self, view: ProtocolView, item: NormalizedNode) -> None:
        view.skills[item.node_id] = SkillSpec(
            skill_id=item.node_id,
            title=str(item.fields.get("title") or item.node_id),
            summary=str(item.fields.get("summary") or ""),
            context=str(item.fields.get("context") or ""),
            child_skills=list(item.fields.get("child_skills") or []),
            refs=list(item.fields.get("refs") or []),
            tools=list(item.fields.get("tools") or []),
            knowledge_nodes=list(item.fields.get("knowledge_nodes") or []),
            source_node=item.node.node_id,
            markdown_body=item.node.body,
            source_path=item.node.source_path,
        )

    def _add_toolbox(self, view: ProtocolView, item: NormalizedNode) -> None:
        toolbox_id = item.node_id
        if toolbox_id.startswith("tool/"):
            # Prefer Runtime id if present. Otherwise infer from path.
            toolbox_id = str(item.node.runtime_block.get("id") or item.fields.get("toolbox_id") or item.node_id.rsplit("/", 1)[-1])
            if toolbox_id == "runtime":
                toolbox_id = "engine"
        view.toolboxes[toolbox_id] = ToolboxSpec(
            toolbox_id=toolbox_id,
            title=str(item.fields.get("title") or toolbox_id),
            module=str(item.fields.get("module") or ""),
            class_name=str(item.fields.get("class_name") or ""),
            tool_ids=list(item.fields.get("tool_ids") or []),
            category=str(item.fields.get("category") or ""),
            source_node=item.node.node_id,
        )

    def _add_tool(self, view: ProtocolView, item: NormalizedNode) -> None:
        tool_id = item.node_id
        if not tool_id or "/" in tool_id:
            view.diagnostics.append(ProtocolDiagnostic("error", item.node.node_id, "Tool Wiki Page cannot infer tool id.", "Add Runtime id or a dotted Tool entry.", "id"))
            return
        view.tools[tool_id] = ToolSpec(
            tool_id=tool_id,
            title=str(item.fields.get("title") or tool_id),
            description=str(item.fields.get("summary") or item.fields.get("context") or tool_id),
            input_schema=dict(item.fields.get("input_schema") or {"type": "object", "properties": {}}),
            output_schema=dict(item.fields.get("output_schema") or {}),
            executor=None,
            toolbox=str(item.fields.get("toolbox") or tool_id.split(".", 1)[0]),
            permission_level=int(item.fields.get("permission_level") or 1),
            categories=tuple(str(x) for x in (item.fields.get("categories") or ())),
            activation_mode=str(item.fields.get("activation_mode") or "skill"),
            activation_rules=tuple(str(x) for x in (item.fields.get("activation_rules") or ())),
            priority=int(item.fields.get("priority") or 50),
            safety=str(item.fields.get("safety") or ""),
            context_hint=str(item.fields.get("context_hint") or ""),
            source_node=item.node.node_id,
        )


    def _discover_python_toolboxes(self, view: ProtocolView) -> None:
        for module in self._iter_tool_modules():
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if not is_toolbox_class(module.__name__, obj):
                    continue
                toolbox_name = str(getattr(obj, "toolbox_name"))
                self.toolbox_classes[toolbox_name] = obj
                view.toolboxes.setdefault(
                    toolbox_name,
                    ToolboxSpec(
                        toolbox_id=toolbox_name,
                        title=toolbox_name,
                        module=obj.__module__,
                        class_name=obj.__name__,
                        category=self._category_from_module(obj.__module__),
                        source_node="python:" + obj.__module__,
                    ),
                )
                view.toolboxes[toolbox_name].module = obj.__module__
                view.toolboxes[toolbox_name].class_name = obj.__name__
                # Tool executors are attached during RuntimeKernel installation.
                # Protocol compile must not instantiate external adapters.
    def _iter_tool_modules(self):
        for package_name in TOOL_PACKAGES:
            try:
                package = importlib.import_module(package_name)
            except Exception:
                continue
            yield package
            if not hasattr(package, "__path__"):
                continue
            for info in pkgutil.walk_packages(package.__path__, prefix=f"{package_name}."):
                yield importlib.import_module(info.name)

    @staticmethod
    def _category_from_module(module: str) -> str:
        for item in ("external", "workflow", "system"):
            if f".{item}." in module or module.endswith(f".{item}"):
                return item
        return "external"

    def _validate(self, view: ProtocolView) -> None:
        for agent in view.agents.values():
            if not agent.root_skill:
                view.diagnostics.append(ProtocolDiagnostic("error", agent.source_node, "Agent missing root skill.", "Add Root or Runtime root_skill.", "root_skill"))
            elif agent.root_skill not in view.skills:
                view.diagnostics.append(ProtocolDiagnostic("error", agent.source_node, f"Agent root skill not found: {agent.root_skill}", "Create the Skill Wiki Page or fix the link.", "root_skill"))

        for skill in view.skills.values():
            for tool_id in skill.tools:
                if tool_id not in view.tools:
                    view.diagnostics.append(ProtocolDiagnostic("warning", skill.source_node, f"Skill references unknown tool: {tool_id}", "Create a Tool Wiki Page or remove the reference.", "tools"))
            for child in skill.child_skills:
                if child not in view.skills:
                    view.diagnostics.append(ProtocolDiagnostic("warning", skill.source_node, f"Skill child not found: {child}", "Create the child Skill Wiki Page or fix link.", "child_skills"))

        for tool_id, spec in view.tools.items():
            if "system" in spec.categories and spec.permission_level < 3:
                view.diagnostics.append(ProtocolDiagnostic("error", spec.source_node or tool_id, f"System tool permission must be >= 3: {tool_id}", "Raise permission_level.", "permission_level"))

    def _build_graph(self, view: ProtocolView, normalized: list[NormalizedNode]) -> None:
        edges: list[dict[str, str]] = []
        for item in normalized:
            for link in item.node.links:
                edges.append({"from": item.node.node_id, "to": link, "kind": "wiki_link"})
        view.graph = ProtocolGraph(edges=edges)
