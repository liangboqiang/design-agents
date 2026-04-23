from __future__ import annotations

from pathlib import Path
from typing import Any

from governance.registry import GovernanceRegistry
from schemas.agent import AgentSpec
from shared.paths import project_root

from ..child_engine_factory import ChildEngineFactory
from ..control_actions import build_control_action_specs
from ..engine_builder import EngineBuildRequest, EngineBuilder, EngineRuntimeBundle
from ..engine_control import EngineControlService
from ..harness import Harness


class Engine:
    """Runtime facade."""

    def __init__(
        self,
        *,
        bundle: EngineRuntimeBundle,
        enhancement_names: list[str],
        persistent_worker: bool = False,
    ):
        self.registry = bundle.registry
        self.agent_spec = bundle.agent_spec
        self.settings = bundle.settings
        self.session = bundle.session
        self.context = bundle.context
        self.engine_id = bundle.context.engine_id
        self.provider = bundle.settings.provider
        self.model = bundle.settings.model
        self.api_key = bundle.settings.api_key
        self.base_url = bundle.settings.base_url
        self.persistent_worker = persistent_worker
        self.enhancement_names = list(enhancement_names)

        self.llm = bundle.llm
        self.knowledge_hub = bundle.knowledge_hub
        self.wiki_hub = bundle.knowledge_hub
        self.skill_runtime = bundle.skill_runtime
        self.tool_index = bundle.tool_index
        self.surface_resolver = bundle.surface_resolver
        self.context_assembler = bundle.context_assembler
        self.response_parser = bundle.response_parser
        self.normalizer = bundle.normalizer
        self.audit = bundle.audit
        self.events = bundle.events
        self.runtime_state = bundle.runtime_state
        self.action_registry = bundle.action_registry
        self.toolboxes = bundle.toolboxes
        self.capabilities = bundle.capabilities
        self.core_participants = bundle.core_participants
        self.lifecycle = bundle.lifecycle
        self.dispatcher = bundle.dispatcher
        self.harness_ports = None
        self.harness = None
        self.control = None
        self.child_factory = None
        self.failure_sink = bundle.failure_sink
        self.fault_boundary = bundle.fault_boundary

    @classmethod
    def from_agent_spec(cls, spec: AgentSpec, **overrides) -> "Engine":
        llm_overrides = dict(spec.llm)
        llm_overrides.update(
            {key: overrides.pop(key) for key in list(overrides.keys()) if key in {"provider", "model", "api_key", "base_url"}}
        )
        request = EngineBuildRequest(
            skill_root=overrides.pop("skill_root", spec.root_skill),
            provider=llm_overrides.get("provider"),
            model=llm_overrides.get("model"),
            api_key=llm_overrides.get("api_key"),
            base_url=llm_overrides.get("base_url"),
            user_id=overrides.pop("user_id", "default_user"),
            conversation_id=overrides.pop("conversation_id", "default_conversation"),
            task_id=overrides.pop("task_id", "default_task"),
            toolboxes=overrides.pop("toolboxes", spec.toolboxes),
            enhancements=overrides.pop("enhancements", spec.capabilities),
            storage_base=overrides.pop("storage_base", None),
            max_steps=overrides.pop("max_steps", 12),
            role_name=overrides.pop("role_name", None),
            persistent_worker=overrides.pop("persistent_worker", False),
            registry=overrides.pop("registry", None),
            agent_spec=spec,
            context_policy=overrides.pop("context_policy", spec.context_policy),
        )
        if overrides:
            unknown = ", ".join(sorted(str(key) for key in overrides))
            raise TypeError(f"Unsupported engine overrides: {unknown}")
        return cls.build(request)

    @classmethod
    def build(cls, request: EngineBuildRequest) -> "Engine":
        builder = EngineBuilder()
        bundle = builder.build_bundle(request)
        enhancement_names = list(request.enhancements or bundle.agent_spec.capabilities or [])
        engine = cls(bundle=bundle, enhancement_names=enhancement_names, persistent_worker=request.persistent_worker)

        builder.install_runtime(engine, request)

        engine.control = EngineControlService(
            registry=engine.registry,
            skill_runtime=engine.skill_runtime,
            context=engine.context,
            events=engine.events,
            action_registry=engine.action_registry,
        )
        for spec in build_control_action_specs(engine.control):
            engine.action_registry[spec.action_id] = spec
        engine.dispatcher.registry = engine.action_registry

        engine.child_factory = ChildEngineFactory(storage_base=request.storage_base)
        engine.harness = Harness(engine.harness_ports)
        bind = getattr(engine.knowledge_hub, "bind_engine", None)
        if bind is not None:
            bind(engine)
        return engine

    @property
    def last_surface_snapshot(self):
        return self.runtime_state.last_surface_snapshot

    def inspect_skill(self, skill: str) -> str:
        return self.control.inspect_skill(skill)

    def inspect_action(self, action: str) -> str:
        return self.control.inspect_action(action)

    def list_child_skills(self) -> str:
        return self.control.list_child_skills()

    def enter_skill(self, skill: str) -> str:
        return self.control.enter_skill(skill)

    def append_system_note(self, content: str) -> None:
        self.session.history.append_system(content)

    def append_tool_result(self, action: str, content: str) -> None:
        self.session.history.append_tool(action, content)

    def replace_history(self, rows: list[dict]) -> None:
        self.session.history.replace(rows)

    def read_history(self) -> list[dict]:
        return self.session.history.read()

    def read_state_json(self, name: str, default: Any):
        return self.session.read_state_json(name, default)

    def write_state_json(self, name: str, payload: Any) -> None:
        self.session.write_state_json(name, payload)

    def capability(self, name: str):
        for capability in self.capabilities:
            if capability.capability_name == name:
                return capability
        return None

    def has_visible_wiki_actions(self, surface_snapshot) -> bool:
        return any(spec.action_id.startswith("wiki.") or spec.action_id.startswith("wiki_admin.") for spec in surface_snapshot.visible_actions)

    def chat(self, message: str) -> str:
        return self.harness.chat(message)

    def chat_turn(self, message: str, files: list[dict] | None = None) -> str:
        return self.harness.chat(message, files=files)

    def refresh_wiki(self) -> str:
        return self.knowledge_hub.refresh_from_registry()

    def ingest_files(self, files: list[dict] | None) -> str:
        return self.knowledge_hub.ingest_user_files(files)

    def spawn_child(
        self,
        *,
        skill: str | None,
        enhancements: list[str],
        role_name: str,
        persistent_worker: bool = False,
        toolboxes: list[str] | None = None,
    ):
        return self.child_factory.spawn_from_parent(
            self,
            skill=skill,
            enhancements=enhancements or self.enhancement_names,
            role_name=role_name,
            persistent_worker=persistent_worker,
            toolboxes=toolboxes,
        )

    def tick(self) -> str:
        autonomy = self.capability("autonomy")
        if autonomy is None:
            return "Autonomy not enabled."
        result = autonomy.idle_tick()
        if result and not result.startswith("No unclaimed"):
            return self.chat(f"Auto-claimed task detail:\n{result}")
        return result


def load_agent_spec(spec_path: Path) -> AgentSpec:
    spec_path = Path(spec_path).resolve()
    registry = GovernanceRegistry(project_root())
    return registry.get_agent_spec(spec_path.parent.name)
