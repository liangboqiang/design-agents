from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

from control.activation import ActivationPolicy
from control.audit import GovernanceAudit
from control.events import EventBus
from control.normalizer import Normalizer
from control.registry import SpecRegistry
from control.surface import SurfaceResolver
from control.turn_driver import TurnDriver
from control.action_dispatcher import ActionDispatcher
from control.contracts import EngineRuntimeState, TurnRuntimePorts
from control.reply_parser import ReplyParser
from control.turn_guard import FailureSink, TurnGuard
from control.turn_lifecycle import TurnLifecycle
from control.turn_policy import TurnPolicy, build_control_action_specs
from llm.config import resolve_llm_config
from llm.factory import LLMFactory
from context.knowledge import KnowledgePicker
from context.surface_assembler import SurfaceAssembler
from context.assembler import ContextAssembler
from schemas.action import ActionSpec
from schemas.agent import AgentSpec
from schemas.runtime import EngineContext, EngineSettings
from shared.ids import new_id
from shared.paths import project_root
from tool.indexes.toolbox_registry import Toolbox

from control.capabilities.base import Capability
from control.capabilities.registry import create_capability
from .child_factory import ChildFactory
from .participant_set import AttachmentIngressParticipant, ParticipantSet
from .service_hub import AttachmentIngestionService, KnowledgeHubService
from .session_state import SessionState
from .skill_state import SkillState


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
    context_policy: dict[str, Any]
    settings: EngineSettings
    session: SessionState
    context: EngineContext
    knowledge_hub: KnowledgeHubService
    skill_state: SkillState
    events: EventBus
    runtime_state: EngineRuntimeState = field(default_factory=EngineRuntimeState)
    enhancement_names: list[str] = field(default_factory=list)
    toolbox_names: list[str] = field(default_factory=list)
    _spawn_child: Callable[..., Any] | None = None

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

    def spawn_child(
        self,
        *,
        skill: str | None,
        enhancements: list[str],
        role_name: str,
        toolboxes: list[str] | None = None,
    ):
        if self._spawn_child is None:
            raise RuntimeError("Child spawning is not installed on this runtime host.")
        return self._spawn_child(
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

        runtime = self.build_bundle(request)
        turn_driver, capability_lookup = self.install_runtime(runtime, request)

        def tick() -> str:
            autonomy = capability_lookup("autonomy")
            if autonomy is None:
                return "Autonomy not enabled."
            result = autonomy.idle_tick()
            if result and not result.startswith("No unclaimed"):
                return turn_driver.chat(f"Auto-claimed task detail:\n{result}")
            return result

        return engine_cls(
            chat=turn_driver.chat,
            tick=tick,
            spawn_child=runtime.spawn_child,
        )

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
        skill_state = SkillState(registry, root_skill_id, audit)
        engine_id = request.role_name or new_id("engine")
        context = EngineContext(
            engine_id=engine_id,
            root_skill_id=root_skill_id,
            active_skill_id=skill_state.active_skill_id,
            settings=settings,
            paths=session.paths,
            agent_name=agent_spec.name,
            agent_context=agent_spec.context_body,
        )
        knowledge_hub = KnowledgeHubService(project_root=project_root(), registry=registry, session=session)
        return RuntimeHost(
            registry=registry,
            context_policy=dict(agent_spec.context_policy or {}),
            settings=settings,
            session=session,
            context=context,
            knowledge_hub=knowledge_hub,
            skill_state=skill_state,
            events=events,
            runtime_state=runtime_state,
            enhancement_names=list(agent_spec.capabilities or []),
            toolbox_names=list(agent_spec.toolboxes or ["files", "shell"]),
        )

    def install_runtime(self, runtime: RuntimeHost, request: EngineBuildRequest):
        audit = runtime.skill_state.audit
        normalizer = Normalizer()
        llm = LLMFactory.create(runtime.provider, runtime.model, runtime.api_key, runtime.base_url)
        surface_assembler = SurfaceAssembler(SurfaceResolver(runtime.registry, ActivationPolicy(), audit))
        knowledge_picker = KnowledgePicker()
        context_assembler = ContextAssembler(max_prompt_chars=runtime.settings.max_prompt_chars)
        reply_parser = ReplyParser()
        failure_sink = FailureSink(session=runtime.session, audit=audit, events=runtime.events, runtime_state=runtime.runtime_state)
        fault_boundary = TurnGuard(failure_sink)
        runtime.events.set_fault_reporter(fault_boundary.report)

        child_factory = ChildFactory(storage_base=request.storage_base)
        runtime._spawn_child = lambda **kwargs: child_factory.spawn_from_parent(runtime, **kwargs)

        requested_toolboxes = list(request.toolboxes if request.toolboxes is not None else runtime.toolbox_names)
        runtime.enhancement_names = list(request.enhancements or runtime.enhancement_names or [])

        toolboxes = self._prepare_toolboxes(runtime, requested_toolboxes)
        runtime.toolbox_names = [toolbox.toolbox_name for toolbox in toolboxes]
        capabilities = self._prepare_capabilities(runtime, runtime.enhancement_names)
        capability_by_name = {capability.capability_name: capability for capability in capabilities}
        for capability in capabilities:
            capability.bind(runtime, capability_by_name.get)

        participants = self._prepare_participants(runtime)
        participant_set = ParticipantSet(core=list(participants))
        lifecycle = TurnLifecycle(
            [*participant_set.all(), *capabilities],
            fault_reporter=fault_boundary.report,
        )

        action_registry: dict[str, ActionSpec] = {}
        for toolbox in toolboxes:
            specs = list(toolbox.action_specs())
            self._register_many(action_registry, specs)

        for capability in capabilities:
            self._register_many(action_registry, capability.action_specs())

        control = TurnPolicy(
            registry=runtime.registry,
            skill_state=runtime.skill_state,
            context=runtime.context,
            events=runtime.events,
            action_registry=action_registry,
        )
        for spec in build_control_action_specs(control):
            action_registry[spec.action_id] = spec

        dispatcher = ActionDispatcher(action_registry, fault_reporter=fault_boundary.report)

        def assemble_surface(state_fragments: list[str]):
            surface = surface_assembler.assemble_surface(
                skill_state=runtime.skill_state,
                action_registry=action_registry,
                state_fragments=state_fragments,
                recent_events=runtime.events.recent(),
            )
            runtime.runtime_state.last_surface_snapshot = surface
            return surface

        def build_system_prompt(surface, state_fragments: list[str]):  # noqa: ANN001
            selection = knowledge_picker.pick(surface_snapshot=surface, knowledge_hub=runtime.knowledge_hub)
            return context_assembler.build_system_prompt(
                engine_context=runtime.context,
                skill_state=runtime.skill_state,
                surface_snapshot=surface,
                history_rows=runtime.session.history.read(),
                state_fragments=state_fragments,
                recent_events=runtime.events.recent(),
                audit=audit,
                registry=runtime.registry,
                knowledge_brief=selection.brief,
                knowledge_actions_visible=selection.actions_visible,
            )

        ports = TurnRuntimePorts(
            lifecycle=lifecycle,
            fault_boundary=fault_boundary,
            emit_event=runtime.events.emit,
            active_skill_id=lambda: runtime.skill_state.active_skill_id,
            history=runtime.session.history,
            max_steps=runtime.settings.max_steps,
            model_name=runtime.settings.model,
            assemble_surface=assemble_surface,
            build_system_prompt=build_system_prompt,
            build_messages=lambda: context_assembler.build_messages(
                runtime.session.history.read(),
                runtime.settings.history_keep_turns,
            ),
            complete_model=llm.complete,
            parse_reply=reply_parser.parse,
            dispatch_action=dispatcher.dispatch,
            normalize_tool_result=lambda action, content: normalizer.normalize_tool_result(action, content, limit=8_000),
            record_audit=audit.record,
        )
        return TurnDriver(ports), capability_by_name.get

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
            prepared.append(create_capability(name))
        return prepared

    @staticmethod
    def _prepare_participants(runtime: RuntimeHost) -> list[object]:
        attachment_service = AttachmentIngestionService(knowledge_hub=runtime.knowledge_hub, session=runtime.session)
        participants = [AttachmentIngressParticipant(attachment_service)]
        for participant in participants:
            bind = getattr(participant, "bind_runtime", None)
            if bind is not None:
                bind(runtime)
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
