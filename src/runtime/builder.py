from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from governance.activation import ActivationPolicy
from governance.audit import GovernanceAudit
from governance.events import EventBus
from governance.normalizer import Normalizer
from governance.registry import GovernanceRegistry
from governance.surface import SurfaceResolver
from harness.action_dispatcher import ActionDispatcher
from harness.contracts import EngineRuntimeState, TurnRuntimePorts
from harness.reply_parser import ReplyParser
from harness.turn_guard import FailureSink, TurnGuard
from harness.turn_lifecycle import TurnLifecycle
from llm.config import resolve_llm_config
from llm.factory import LLMFactory
from prompt.surface_assembler import SurfaceAssembler
from prompt.prompt_assembler import PromptAssembler
from schemas.action import ActionSpec
from schemas.agent import AgentSpec
from schemas.runtime import EngineContext, EngineSettings
from shared.ids import new_id
from shared.paths import project_root
from tool.indexes.tool_index import ToolIndex
from tool.indexes.toolbox_registry import Toolbox

from .capabilities.base import Capability
from .capabilities.registry import create_capability
from .participant_set import AttachmentIngressParticipant, ParticipantSet
from .services import AttachmentIngestionService, KnowledgeHubService
from .service_hub import ServiceHub
from .session_state import SessionState
from .skill_state import SkillState
from .toolbox_hub import ToolboxHub


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
    session: SessionState
    context: EngineContext
    llm: Any
    knowledge_hub: KnowledgeHubService
    service_hub: ServiceHub
    skill_state: SkillState
    tool_index: ToolIndex
    toolbox_hub: ToolboxHub
    surface_resolver: SurfaceResolver
    surface_assembler: SurfaceAssembler
    prompt_assembler: PromptAssembler
    reply_parser: ReplyParser
    normalizer: Normalizer
    audit: GovernanceAudit
    events: EventBus
    runtime_state: EngineRuntimeState = field(default_factory=EngineRuntimeState)
    failure_sink: FailureSink | None = None
    fault_boundary: TurnGuard | None = None
    action_registry: dict[str, ActionSpec] = field(default_factory=dict)
    toolboxes: list[Toolbox] = field(default_factory=list)
    capabilities: list[Capability] = field(default_factory=list)
    participants: list[object] = field(default_factory=list)
    lifecycle: TurnLifecycle | None = None
    dispatcher: ActionDispatcher | None = None


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
        session = SessionState(settings, storage_root)
        runtime_state = EngineRuntimeState()
        audit = GovernanceAudit()
        events = EventBus()
        normalizer = Normalizer()
        skill_state = SkillState(registry, root_skill_id, audit)
        engine_id = request.role_name or new_id("engine")
        context = EngineContext(
            engine_id=engine_id,
            root_skill_id=root_skill_id,
            active_skill_id=skill_state.active_skill_id,
            settings=settings,
            paths=session.paths,
            agent_name=agent_spec.name,
        )
        llm = LLMFactory.create(llm_config.provider, llm_config.model, llm_config.api_key, llm_config.base_url)
        knowledge_hub = KnowledgeHubService(project_root=project_root(), registry=registry, session=session)
        service_hub = ServiceHub(knowledge_hub=knowledge_hub)
        tool_index = ToolIndex()
        toolbox_hub = ToolboxHub(tool_index=tool_index)
        surface_resolver = SurfaceResolver(registry, ActivationPolicy(), audit)
        failure_sink = FailureSink(session=session, audit=audit, events=events, runtime_state=runtime_state)
        fault_boundary = TurnGuard(failure_sink)
        events.set_fault_reporter(fault_boundary.report)
        return EngineRuntimeBundle(
            registry=registry,
            agent_spec=agent_spec,
            settings=settings,
            session=session,
            context=context,
            llm=llm,
            knowledge_hub=knowledge_hub,
            service_hub=service_hub,
            skill_state=skill_state,
            tool_index=tool_index,
            toolbox_hub=toolbox_hub,
            surface_resolver=surface_resolver,
            surface_assembler=SurfaceAssembler(surface_resolver),
            prompt_assembler=PromptAssembler(registry.context_root, max_prompt_chars=max_prompt_chars),
            reply_parser=ReplyParser(),
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
        engine.toolbox_hub.toolboxes = list(engine.toolboxes)
        engine.participants = self._prepare_participants(engine)
        engine.participant_set = ParticipantSet(core=list(engine.participants))
        engine.lifecycle = TurnLifecycle(
            [*engine.participant_set.all(), *engine.capabilities],
            fault_reporter=engine.fault_boundary.report,
        )

        for toolbox in engine.toolboxes:
            specs = list(toolbox.action_specs())
            engine.tool_index.register_toolbox_actions(toolbox.toolbox_name, specs)
            self._register_many(engine.action_registry, specs)

        for capability in engine.capabilities:
            self._register_many(engine.action_registry, capability.action_specs())

        engine.dispatcher = ActionDispatcher(engine.action_registry, fault_reporter=engine.fault_boundary.report)
        engine.harness_ports = TurnRuntimePorts(
            lifecycle=engine.lifecycle,
            events=engine.events,
            skill_state=engine.skill_state,
            session=engine.session,
            settings=engine.settings,
            surface_resolver=engine.surface_resolver,
            surface_assembler=engine.surface_assembler,
            prompt_assembler=engine.prompt_assembler,
            llm=engine.llm,
            reply_parser=engine.reply_parser,
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
            rel = str(candidate.resolve().relative_to(registry.skills_root.resolve())).replace("\\", "/")
            return f"skill/{rel}"
        relative_candidates = [
            registry.skills_root / candidate,
            project_root() / candidate,
        ]
        for option in relative_candidates:
            if option.is_dir() and (option / "page.md").exists():
                rel = str(option.resolve().relative_to(registry.skills_root.resolve())).replace("\\", "/")
                return f"skill/{rel}"
        if skill_text.endswith("/page.md"):
            option = Path(skill_text).parent.resolve()
            rel = str(option.relative_to(registry.skills_root.resolve())).replace("\\", "/")
            return f"skill/{rel}"
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
    def _prepare_participants(engine) -> list[object]:  # noqa: ANN001
        attachment_service = AttachmentIngestionService(knowledge_hub=engine.knowledge_hub, session=engine.session)
        participants = [AttachmentIngressParticipant(attachment_service)]
        for participant in participants:
            bind = getattr(participant, "bind", None)
            if bind is not None:
                bind(engine)
        engine.service_hub.attachment_ingestion = attachment_service
        return participants
