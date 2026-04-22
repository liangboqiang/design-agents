from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from context.assembler.context_assembler import ContextAssembler
from governance.activation import ActivationPolicy
from governance.audit import GovernanceAudit
from governance.events import EventBus
from governance.normalizer import Normalizer
from governance.registry import GovernanceRegistry
from governance.surface_resolver import SurfaceResolver
from llm.config import resolve_llm_config
from llm.factory import LLMFactory
from schemas.action import ActionSpec
from schemas.agent import AgentSpec
from schemas.runtime import EngineContext, EngineSettings
from shared.ids import new_id
from shared.paths import project_root
from tools.indexes.tool_index import ToolIndex
from tools.indexes.toolbox_registry import Toolbox

from .capabilities.base import Capability
from .capabilities.registry import create_capability
from .core_participants import AttachmentIngressParticipant
from .dispatcher import Dispatcher
from .engine_ports import EngineRuntimeState, TurnRuntimePorts
from .failure_sink import FailureSink
from .fault_boundary import FaultBoundary
from .lifecycle import LifecycleManager
from .response_parser import ResponseParser
from .services import AttachmentIngestionService, KnowledgeHubService
from .session_runtime import SessionRuntime
from .skill_runtime import SkillRuntime


@dataclass(slots=True)
class EngineBuildRequest:
    skill_root: str | Path
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    user_id: str = "default_user"
    conversation_id: str = "default_conversation"
    task_id: str = "default_task"
    toolboxes: list[str | Toolbox] | None = None
    enhancements: list[str] | None = None
    storage_base: Path | None = None
    max_steps: int = 12
    role_name: str | None = None
    persistent_worker: bool = False
    registry: GovernanceRegistry | None = None
    agent_spec: AgentSpec | None = None
    context_policy: dict[str, Any] | None = None


@dataclass(slots=True)
class EngineRuntimeBundle:
    registry: GovernanceRegistry
    agent_spec: AgentSpec
    settings: EngineSettings
    session: SessionRuntime
    context: EngineContext
    llm: Any
    knowledge_hub: KnowledgeHubService
    skill_runtime: SkillRuntime
    tool_index: ToolIndex
    surface_resolver: SurfaceResolver
    context_assembler: ContextAssembler
    response_parser: ResponseParser
    normalizer: Normalizer
    audit: GovernanceAudit
    events: EventBus
    runtime_state: EngineRuntimeState = field(default_factory=EngineRuntimeState)
    failure_sink: FailureSink | None = None
    fault_boundary: FaultBoundary | None = None
    action_registry: dict[str, ActionSpec] = field(default_factory=dict)
    toolboxes: list[Toolbox] = field(default_factory=list)
    capabilities: list[Capability] = field(default_factory=list)
    core_participants: list[object] = field(default_factory=list)
    lifecycle: LifecycleManager | None = None
    dispatcher: Dispatcher | None = None


class EngineBuilder:
    def build_bundle(self, request: EngineBuildRequest) -> EngineRuntimeBundle:
        registry = request.registry or GovernanceRegistry(project_root())
        root_skill_id = self._resolve_skill_id(registry, request.skill_root)
        agent_spec = request.agent_spec or AgentSpec(name="ad_hoc", root_skill=root_skill_id)
        llm_config = resolve_llm_config(request.provider, request.model, request.api_key, request.base_url)
        context_policy = dict(request.context_policy or agent_spec.context_policy or {})
        max_prompt_chars = int(context_policy.get("max_prompt_chars", 18_000))
        settings = EngineSettings(
            provider=llm_config.provider,
            model=llm_config.model,
            api_key=llm_config.api_key,
            base_url=llm_config.base_url,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            task_id=request.task_id,
            max_steps=request.max_steps,
            max_prompt_chars=max_prompt_chars,
        )
        storage_root = (request.storage_base or project_root() / ".runtime_data").resolve()
        session = SessionRuntime(settings, storage_root)
        runtime_state = EngineRuntimeState()
        audit = GovernanceAudit()
        events = EventBus()
        normalizer = Normalizer()
        skill_runtime = SkillRuntime(registry, root_skill_id, audit)
        engine_id = request.role_name or new_id("engine")
        context = EngineContext(
            engine_id=engine_id,
            root_skill_id=root_skill_id,
            active_skill_id=skill_runtime.active_skill_id,
            settings=settings,
            paths=session.paths,
            agent_name=agent_spec.name,
        )
        llm = LLMFactory.create(llm_config.provider, llm_config.model, llm_config.api_key, llm_config.base_url)
        knowledge_hub = KnowledgeHubService(project_root=project_root(), registry=registry, session=session)
        knowledge_hub.ensure_bootstrap()
        knowledge_hub.refresh_from_registry()
        failure_sink = FailureSink(session=session, audit=audit, events=events, runtime_state=runtime_state)
        fault_boundary = FaultBoundary(failure_sink)
        events.set_fault_reporter(fault_boundary.report)
        return EngineRuntimeBundle(
            registry=registry,
            agent_spec=agent_spec,
            settings=settings,
            session=session,
            context=context,
            llm=llm,
            knowledge_hub=knowledge_hub,
            skill_runtime=skill_runtime,
            tool_index=ToolIndex(),
            surface_resolver=SurfaceResolver(registry, ActivationPolicy(), audit),
            context_assembler=ContextAssembler(registry.context_root / "templates", max_prompt_chars=max_prompt_chars),
            response_parser=ResponseParser(),
            normalizer=normalizer,
            audit=audit,
            events=events,
            runtime_state=runtime_state,
            failure_sink=failure_sink,
            fault_boundary=fault_boundary,
        )

    def install_runtime(self, engine, request: EngineBuildRequest) -> None:  # noqa: ANN001
        requested_toolboxes = list(request.toolboxes if request.toolboxes is not None else (engine.agent_spec.toolboxes or ["files", "shell"]))
        enhancement_names = list(request.enhancements or engine.agent_spec.capabilities or [])

        engine.toolboxes = self._prepare_toolboxes(engine, requested_toolboxes)
        engine.capabilities = self._prepare_capabilities(engine, enhancement_names)
        engine.core_participants = self._prepare_core_participants(engine)
        engine.lifecycle = LifecycleManager(
            [*engine.core_participants, *engine.capabilities],
            fault_reporter=engine.fault_boundary.report,
        )

        for toolbox in engine.toolboxes:
            specs = list(toolbox.action_specs())
            engine.tool_index.register_toolbox_actions(toolbox.toolbox_name, specs)
            self._register_many(engine.action_registry, specs)

        for capability in engine.capabilities:
            self._register_many(engine.action_registry, capability.action_specs())

        engine.dispatcher = Dispatcher(engine.action_registry, fault_reporter=engine.fault_boundary.report)
        engine.harness_ports = TurnRuntimePorts(
            lifecycle=engine.lifecycle,
            events=engine.events,
            skill_runtime=engine.skill_runtime,
            session=engine.session,
            settings=engine.settings,
            surface_resolver=engine.surface_resolver,
            context_assembler=engine.context_assembler,
            llm=engine.llm,
            response_parser=engine.response_parser,
            dispatcher=engine.dispatcher,
            normalizer=engine.normalizer,
            audit=engine.audit,
            context=engine.context,
            registry=engine.registry,
            knowledge_hub=engine.knowledge_hub,
            action_registry=engine.action_registry,
            state=engine.runtime_state,
            failure_sink=engine.failure_sink,
            fault_boundary=engine.fault_boundary,
        )

    @staticmethod
    def _register_many(registry: dict[str, ActionSpec], specs: Iterable[ActionSpec]) -> None:
        for spec in specs:
            registry[spec.action_id] = spec

    @staticmethod
    def _resolve_skill_id(registry: GovernanceRegistry, skill_root: str | Path) -> str:
        if isinstance(skill_root, Path):
            candidate = skill_root
        else:
            candidate = Path(str(skill_root))
        skill_text = str(skill_root).replace("\\", "/")
        if skill_text in registry.skills:
            return skill_text
        if candidate.is_absolute() and candidate.is_dir():
            return str(candidate.resolve().relative_to(registry.skills_root.resolve())).replace("\\", "/")
        relative_candidates = [
            registry.skills_root / candidate,
            project_root() / candidate,
        ]
        for option in relative_candidates:
            if option.is_dir() and (option / "SKILL.md").exists():
                return str(option.resolve().relative_to(registry.skills_root.resolve())).replace("\\", "/")
        if skill_text.endswith("/SKILL.md"):
            option = Path(skill_text).parent.resolve()
            return str(option.relative_to(registry.skills_root.resolve())).replace("\\", "/")
        raise ValueError(f"Unknown skill root: {skill_root}")

    @staticmethod
    def _prepare_toolboxes(engine, toolboxes: Iterable[str | Toolbox]) -> list[Toolbox]:  # noqa: ANN001
        prepared: list[Toolbox] = []
        for item in toolboxes:
            if isinstance(item, str):
                toolbox = engine.registry.toolbox_registry.create(item, engine.session.workspace_root)
            else:
                toolbox = item if item.workspace_root == engine.session.workspace_root else item.spawn(engine.session.workspace_root)
            toolbox.bind_engine(engine)
            prepared.append(toolbox)
        return prepared

    @staticmethod
    def _prepare_capabilities(engine, names: Iterable[str]) -> list[Capability]:  # noqa: ANN001
        prepared: list[Capability] = []
        for name in names:
            capability = create_capability(name)
            capability.bind(engine)
            prepared.append(capability)
        return prepared

    @staticmethod
    def _prepare_core_participants(engine) -> list[object]:  # noqa: ANN001
        attachment_service = AttachmentIngestionService(knowledge_hub=engine.knowledge_hub, session=engine.session)
        participants = [AttachmentIngressParticipant(attachment_service)]
        for participant in participants:
            bind = getattr(participant, "bind", None)
            if bind is not None:
                bind(engine)
        return participants
