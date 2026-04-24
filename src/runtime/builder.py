from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from governance.activation import ActivationPolicy
from governance.audit import GovernanceAudit
from governance.events import EventBus
from governance.normalizer import Normalizer
from governance.registry import SpecRegistry
from governance.surface import SurfaceResolver
from harness.turn_driver import TurnDriver
from harness.action_dispatcher import ActionDispatcher
from harness.contracts import EngineRuntimeState, TurnRuntimePorts
from harness.reply_parser import ReplyParser
from harness.turn_guard import FailureSink, TurnGuard
from harness.turn_lifecycle import TurnLifecycle
from harness.turn_policy import TurnPolicy, build_control_action_specs
from llm.config import resolve_llm_config
from llm.factory import LLMFactory
from prompt.knowledge_picker import KnowledgePicker
from prompt.surface_assembler import SurfaceAssembler
from prompt.prompt_assembler import PromptAssembler
from schemas.action import ActionSpec
from schemas.agent import AgentSpec
from schemas.runtime import EngineContext, EngineSettings
from shared.ids import new_id
from shared.paths import project_root
from tool.indexes.tool_index import ToolIndex
from tool.indexes.toolbox_registry import Toolbox

from harness.capabilities.base import Capability
from harness.capabilities.registry import create_capability
from .child_factory import ChildFactory
from .participant_set import AttachmentIngressParticipant, ParticipantSet
from .service_hub import AttachmentIngestionService, KnowledgeHubService, ServiceHub
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
    registry: SpecRegistry | None = None
    agent_spec: AgentSpec | None = None
    context_policy: dict[str, Any] | None = None


@dataclass(slots=True)
class RuntimeHost:
    registry: SpecRegistry
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
    surface_assembler: SurfaceAssembler
    knowledge_picker: KnowledgePicker
    prompt_assembler: PromptAssembler
    reply_parser: ReplyParser
    normalizer: Normalizer
    audit: GovernanceAudit
    events: EventBus
    runtime_state: EngineRuntimeState = field(default_factory=EngineRuntimeState)
    fault_boundary: TurnGuard | None = None
    action_registry: dict[str, ActionSpec] = field(default_factory=dict)
    toolboxes: list[Toolbox] = field(default_factory=list)
    capabilities: list[Capability] = field(default_factory=list)
    enhancement_names: list[str] = field(default_factory=list)
    harness: TurnDriver | None = None
    child_factory: ChildFactory | None = None

    @property
    def engine_id(self) -> str:
        return self.context.engine_id

    @property
    def provider(self) -> str:
        return self.settings.provider

    @property
    def model(self) -> str:
        return self.settings.model

    @property
    def api_key(self) -> str | None:
        return self.settings.api_key

    @property
    def base_url(self) -> str | None:
        return self.settings.base_url

    def capability(self, name: str):
        return next((item for item in self.capabilities if item.capability_name == name), None)

    def spawn_child(
        self,
        *,
        skill: str | None,
        enhancements: list[str],
        role_name: str,
        toolboxes: list[str] | None = None,
    ):
        return self.child_factory.spawn_from_parent(
            self,
            skill=skill,
            enhancements=enhancements or self.enhancement_names,
            role_name=role_name,
            toolboxes=toolboxes,
        )


class RuntimeBuilder:
    def build_engine(self, request: EngineBuildRequest, *, engine_cls=None):  # noqa: ANN001
        if engine_cls is None:
            from .engine import Engine

            engine_cls = Engine

        bundle = self.build_bundle(request)
        self.install_runtime(bundle, request)
        engine = engine_cls(runtime=bundle)
        return engine

    def build_bundle(self, request: EngineBuildRequest) -> RuntimeHost:
        registry = request.registry or SpecRegistry(project_root())
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
        return RuntimeHost(
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
            surface_assembler=SurfaceAssembler(surface_resolver),
            knowledge_picker=KnowledgePicker(),
            prompt_assembler=PromptAssembler(registry.context_root, max_prompt_chars=max_prompt_chars),
            reply_parser=ReplyParser(),
            normalizer=normalizer,
            audit=audit,
            events=events,
            runtime_state=runtime_state,
            fault_boundary=fault_boundary,
        )

    def install_runtime(self, runtime: RuntimeHost, request: EngineBuildRequest) -> None:
        requested_toolboxes = list(request.toolboxes if request.toolboxes is not None else (runtime.agent_spec.toolboxes or ["files", "shell"]))
        runtime.enhancement_names = list(request.enhancements or runtime.agent_spec.capabilities or [])

        runtime.toolboxes = self._prepare_toolboxes(runtime, requested_toolboxes)
        runtime.capabilities = self._prepare_capabilities(runtime, runtime.enhancement_names)
        runtime.toolbox_hub.toolboxes = list(runtime.toolboxes)
        participants = self._prepare_participants(runtime)
        participant_set = ParticipantSet(core=list(participants))
        lifecycle = TurnLifecycle(
            [*participant_set.all(), *runtime.capabilities],
            fault_reporter=runtime.fault_boundary.report,
        )

        for toolbox in runtime.toolboxes:
            specs = list(toolbox.action_specs())
            runtime.tool_index.register_toolbox_actions(toolbox.toolbox_name, specs)
            self._register_many(runtime.action_registry, specs)

        for capability in runtime.capabilities:
            self._register_many(runtime.action_registry, capability.action_specs())

        control = TurnPolicy(
            registry=runtime.registry,
            skill_state=runtime.skill_state,
            context=runtime.context,
            events=runtime.events,
            action_registry=runtime.action_registry,
        )
        for spec in build_control_action_specs(control):
            runtime.action_registry[spec.action_id] = spec

        dispatcher = ActionDispatcher(runtime.action_registry, fault_reporter=runtime.fault_boundary.report)
        ports = TurnRuntimePorts(
            lifecycle=lifecycle,
            events=runtime.events,
            skill_state=runtime.skill_state,
            session=runtime.session,
            settings=runtime.settings,
            surface_assembler=runtime.surface_assembler,
            knowledge_picker=runtime.knowledge_picker,
            prompt_assembler=runtime.prompt_assembler,
            llm=runtime.llm,
            reply_parser=runtime.reply_parser,
            dispatcher=dispatcher,
            normalizer=runtime.normalizer,
            audit=runtime.audit,
            context=runtime.context,
            registry=runtime.registry,
            knowledge_hub=runtime.knowledge_hub,
            action_registry=runtime.action_registry,
            state=runtime.runtime_state,
            fault_boundary=runtime.fault_boundary,
        )
        runtime.child_factory = ChildFactory(storage_base=request.storage_base)
        runtime.harness = TurnDriver(ports)

    @staticmethod
    def _register_many(registry: dict[str, ActionSpec], specs: Iterable[ActionSpec]) -> None:
        for spec in specs:
            registry[spec.action_id] = spec

    @staticmethod
    def _resolve_skill_id(registry: SpecRegistry, skill_root: str | Path) -> str:
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
    def _prepare_toolboxes(runtime: RuntimeHost, toolboxes: Iterable[str | Toolbox]) -> list[Toolbox]:
        prepared: list[Toolbox] = []
        for item in toolboxes:
            if isinstance(item, str):
                toolbox = runtime.registry.toolbox_registry.create(item, runtime.session.workspace_root)
            else:
                toolbox = item if item.workspace_root == runtime.session.workspace_root else item.spawn(runtime.session.workspace_root)
            toolbox.bind_runtime(runtime)
            prepared.append(toolbox)
        return prepared

    @staticmethod
    def _prepare_capabilities(runtime: RuntimeHost, names: Iterable[str]) -> list[Capability]:
        prepared: list[Capability] = []
        for name in names:
            capability = create_capability(name)
            capability.bind(runtime)
            prepared.append(capability)
        return prepared

    @staticmethod
    def _prepare_participants(runtime: RuntimeHost) -> list[object]:
        attachment_service = AttachmentIngestionService(knowledge_hub=runtime.knowledge_hub, session=runtime.session)
        participants = [AttachmentIngressParticipant(attachment_service)]
        for participant in participants:
            bind = getattr(participant, "bind_runtime", None)
            if bind is not None:
                bind(runtime)
        runtime.service_hub.attachment_ingestion = attachment_service
        return participants


def request_from_agent_spec(spec: AgentSpec, **overrides) -> EngineBuildRequest:
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
        registry=overrides.pop("registry", None),
        agent_spec=spec,
        context_policy=overrides.pop("context_policy", spec.context_policy),
    )
    if overrides:
        unknown = ", ".join(sorted(str(key) for key in overrides))
        raise TypeError(f"Unsupported engine overrides: {unknown}")
    return request


def build_engine(request: EngineBuildRequest):
    return RuntimeBuilder().build_engine(request)
