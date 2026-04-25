from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from llm.config import resolve_llm_config
from llm.factory import LLMFactory
from protocol.registry import RuntimeRegistry
from protocol.types import AgentSpec
from shared.ids import new_id
from .audit import AuditLog
from .dispatcher import ToolDispatcher
from .events import EventBus
from .guard import RuntimeGuard
from .normalizer import Normalizer
from .prompt import PromptCompiler
from .session_state import SessionState
from .state import RuntimeState, SkillState
from .surface import ToolSurface
from .types import EngineContext, EngineSettings, RuntimeRequest
from .service_hub import AttachmentIngestionService, KnowledgeHubService


@dataclass(slots=True)
class RuntimeKernel:
    registry: RuntimeRegistry
    agent: AgentSpec
    settings: EngineSettings
    session: SessionState
    context: EngineContext
    knowledge_hub: KnowledgeHubService
    skill_state: SkillState
    events: EventBus
    audit: AuditLog
    guard: RuntimeGuard
    runtime_state: RuntimeState
    normalizer: Normalizer
    llm: Any
    active_tool_ids: set[str] = field(default_factory=set)
    surface: Any = None
    prompt: Any = None
    dispatcher: Any = None
    engine_id: str = ""

    @classmethod
    def create(cls, request: RuntimeRequest, registry: RuntimeRegistry) -> "RuntimeKernel":
        agent = registry.agent(request.agent_id)
        llm_overrides = dict(agent.llm)
        for key in ("provider", "model", "api_key", "base_url"):
            value = getattr(request, key, None)
            if value is not None:
                llm_overrides[key] = value
        llm_config = resolve_llm_config(
            llm_overrides.get("provider"),
            llm_overrides.get("model"),
            llm_overrides.get("api_key"),
            llm_overrides.get("base_url"),
        )
        policy = dict(agent.policy or {})
        if request.policy:
            policy.update(request.policy)
        settings = EngineSettings(
            provider=llm_config.provider,
            model=llm_config.model,
            api_key=llm_config.api_key,
            base_url=llm_config.base_url,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            task_id=request.task_id,
            max_steps=request.max_steps,
            max_prompt_chars=int(policy.get("max_prompt_chars", 18_000)),
            tool_permission_level=int(policy.get("tool_permission_level", 1)),
            allowed_tool_categories=_tuple(policy.get("allowed_tool_categories", ())),
            denied_tool_categories=_tuple(policy.get("denied_tool_categories", ())),
            allowed_tools=_tuple(policy.get("allowed_tools", ())),
            denied_tools=_tuple(policy.get("denied_tools", ())),
        )
        storage_root = (request.storage_base or registry.project_root / ".runtime_data").resolve()
        session = SessionState(settings, storage_root)
        audit = AuditLog()
        events = EventBus()
        guard = RuntimeGuard(logs_dir=session.paths.logs_dir, audit=audit, events=events)
        skill_state = SkillState(registry, agent.root_skill, audit)
        engine_id = request.role_name or new_id("engine")
        context = EngineContext(
            engine_id=engine_id,
            root_skill_id=agent.root_skill,
            active_skill_id=skill_state.active_skill_id,
            settings=settings,
            paths=session.paths,
            agent_name=agent.agent_id,
            agent_context=agent.context,
        )
        knowledge_hub = KnowledgeHubService(project_root=registry.project_root, registry=registry, session=session)
        kernel = cls(
            registry=registry,
            agent=agent,
            settings=settings,
            session=session,
            context=context,
            knowledge_hub=knowledge_hub,
            skill_state=skill_state,
            events=events,
            audit=audit,
            guard=guard,
            runtime_state=RuntimeState(),
            normalizer=Normalizer(),
            llm=LLMFactory.create(llm_config.provider, llm_config.model, llm_config.api_key, llm_config.base_url),
            engine_id=engine_id,
        )
        kernel._install_toolboxes(request.toolboxes or agent.installation_names())
        kernel.surface = ToolSurface(kernel)
        kernel.prompt = PromptCompiler(kernel)
        kernel.dispatcher = ToolDispatcher(kernel)
        return kernel

    def _install_toolboxes(self, requested: list[str]) -> None:
        toolboxes = _ordered_unique([*requested, "engine"])
        installed: dict[str, Any] = {}
        for name in toolboxes:
            if name not in self.registry.toolbox_classes:
                continue
            extension = self.registry.create_toolbox(name, self.session.workspace_root)
            installed[extension.toolbox_name] = extension
        lookup = installed.get
        for extension in installed.values():
            bind = getattr(extension, "bind_runtime", None)
            if bind:
                try:
                    bind(self, lookup)
                except TypeError:
                    bind(self)
        self.runtime_state.installed_toolboxes = installed
        specs = {}
        for extension in installed.values():
            for spec in extension.tool_specs():
                hard = self.registry.tools.get(spec.tool_id)
                if hard is not None:
                    spec.permission_level = hard.permission_level
                    spec.categories = hard.categories
                    spec.activation_mode = hard.activation_mode
                    spec.activation_rules = hard.activation_rules
                    spec.priority = hard.priority
                    spec.safety = hard.safety
                    spec.context_hint = hard.context_hint
                    spec.output_schema = hard.output_schema
                    spec.source_node = hard.source_node
                specs[spec.tool_id] = spec
        self.runtime_state.tool_registry = specs

    def state_fragments(self) -> list[str]:
        rows: list[str] = []
        for extension in self.runtime_state.installed_toolboxes.values():
            hook = getattr(extension, "state_fragments", None)
            if hook:
                try:
                    rows.extend(hook())
                except Exception:
                    pass
        return self.normalizer.normalize_state_fragments(rows)

    def ingest_attachments(self, files: list[dict] | None) -> str | None:
        if not files:
            return None
        service = AttachmentIngestionService(knowledge_hub=self.knowledge_hub, session=self.session)
        return service.ingest(files)


def _tuple(value) -> tuple[str, ...]:  # noqa: ANN001
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(item) for item in value)


def _ordered_unique(rows: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in rows:
        normalized = str(item).strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            out.append(normalized)
    return out
