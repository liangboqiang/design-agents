from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import yaml

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

from .action_compiler import ActionCompiler
from .capabilities.base import Capability
from .capabilities.registry import create_capability
from .core_participants import AttachmentIngressParticipant
from .dispatcher import Dispatcher
from .harness import Harness
from .lifecycle import LifecycleManager
from .response_parser import ResponseParser
from .services import AttachmentIngestionService, KnowledgeHubService
from .session_runtime import SessionRuntime
from .skill_runtime import SkillRuntime


class Engine:
    def __init__(
        self,
        skill_root: str | Path,
        provider: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        *,
        user_id: str = "default_user",
        conversation_id: str = "default_conversation",
        task_id: str = "default_task",
        toolboxes: list[str | Toolbox] | None = None,
        enhancements: list[str] | None = None,
        storage_base: Path | None = None,
        max_steps: int = 12,
        role_name: str | None = None,
        persistent_worker: bool = False,
        registry: GovernanceRegistry | None = None,
        agent_spec: AgentSpec | None = None,
        context_policy: dict[str, Any] | None = None,
    ):
        self.registry = registry or GovernanceRegistry(project_root())
        self.agent_spec = agent_spec or AgentSpec(name="ad_hoc", root_skill=self._resolve_skill_id(skill_root))
        llm_config = resolve_llm_config(provider, model, api_key, base_url)
        self.provider = llm_config.provider
        self.model = llm_config.model
        self.api_key = llm_config.api_key
        self.base_url = llm_config.base_url
        self.engine_id = role_name or new_id("engine")
        self.persistent_worker = persistent_worker
        self.enhancement_names = [item.strip() for item in (enhancements or self.agent_spec.capabilities or [])]
        max_prompt_chars = int((context_policy or self.agent_spec.context_policy or {}).get("max_prompt_chars", 18_000))
        self.settings = EngineSettings(
            provider=self.provider,
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            user_id=user_id,
            conversation_id=conversation_id,
            task_id=task_id,
            max_steps=max_steps,
            max_prompt_chars=max_prompt_chars,
        )

        storage_root = (storage_base or project_root() / ".runtime_data").resolve()
        self.session = SessionRuntime(self.settings, storage_root)
        root_skill_id = self._resolve_skill_id(skill_root)
        self.audit = GovernanceAudit()
        self.events = EventBus()
        self.normalizer = Normalizer()
        self.skill_runtime = SkillRuntime(self.registry, root_skill_id, self.audit)
        self.context = EngineContext(
            engine_id=self.engine_id,
            root_skill_id=root_skill_id,
            active_skill_id=self.skill_runtime.active_skill_id,
            settings=self.settings,
            paths=self.session.paths,
            agent_name=self.agent_spec.name,
        )
        self.llm = LLMFactory.create(self.provider, self.model, self.api_key, self.base_url)

        self.knowledge_hub = KnowledgeHubService(project_root=project_root(), registry=self.registry, session=self.session)
        self.wiki_hub = self.knowledge_hub
        self.knowledge_hub.ensure_bootstrap()
        self.knowledge_hub.refresh_from_registry()

        requested_toolboxes = list(toolboxes if toolboxes is not None else (self.agent_spec.toolboxes or ["files", "shell"]))
        self.toolboxes = self._prepare_toolboxes(requested_toolboxes)
        self.capabilities = self._prepare_capabilities(self.enhancement_names)
        self.core_participants = self._prepare_core_participants()
        self.lifecycle = LifecycleManager([*self.core_participants, *self.capabilities])
        self.tool_index = ToolIndex()
        self.action_registry: dict[str, ActionSpec] = {}
        self._register_core_actions()
        self._register_toolboxes()
        self._register_capabilities()
        self.surface_resolver = SurfaceResolver(self.registry, ActivationPolicy(), self.audit)
        self.action_compiler = ActionCompiler(self.surface_resolver)
        self.context_assembler = ContextAssembler(self.registry.context_root / "templates", max_prompt_chars=max_prompt_chars)
        self.dispatcher = Dispatcher(self.action_registry)
        self.response_parser = ResponseParser()
        self.harness = Harness(self)
        self.last_surface_snapshot = None

    @classmethod
    def from_agent_spec(cls, spec: AgentSpec, **overrides):
        llm_overrides = dict(spec.llm)
        llm_overrides.update({key: overrides.pop(key) for key in list(overrides.keys()) if key in {"provider", "model", "api_key", "base_url"}})
        return cls(
            skill_root=overrides.pop("skill_root", spec.root_skill),
            provider=llm_overrides.get("provider"),
            model=llm_overrides.get("model"),
            api_key=llm_overrides.get("api_key"),
            base_url=llm_overrides.get("base_url"),
            toolboxes=overrides.pop("toolboxes", spec.toolboxes),
            enhancements=overrides.pop("enhancements", spec.capabilities),
            agent_spec=spec,
            context_policy=overrides.pop("context_policy", spec.context_policy),
            **overrides,
        )

    def _resolve_skill_id(self, skill_root: str | Path) -> str:
        if isinstance(skill_root, Path):
            candidate = skill_root
        else:
            candidate = Path(str(skill_root))
        skill_text = str(skill_root).replace("\\", "/")
        if skill_text in self.registry.skills:
            return skill_text
        if candidate.is_absolute() and candidate.is_dir():
            return str(candidate.resolve().relative_to(self.registry.skills_root.resolve())).replace("\\", "/")
        relative_candidates = [
            self.registry.skills_root / candidate,
            project_root() / candidate,
        ]
        for option in relative_candidates:
            if option.is_dir() and (option / "SKILL.md").exists():
                return str(option.resolve().relative_to(self.registry.skills_root.resolve())).replace("\\", "/")
        if skill_text.endswith("/SKILL.md"):
            option = Path(skill_text).parent.resolve()
            return str(option.relative_to(self.registry.skills_root.resolve())).replace("\\", "/")
        raise ValueError(f"Unknown skill root: {skill_root}")

    def _prepare_toolboxes(self, toolboxes: Iterable[str | Toolbox]) -> list[Toolbox]:
        prepared: list[Toolbox] = []
        for item in toolboxes:
            if isinstance(item, str):
                toolbox = self.registry.toolbox_registry.create(item, self.session.workspace_root)
            else:
                toolbox = item if item.workspace_root == self.session.workspace_root else item.spawn(self.session.workspace_root)
            toolbox.bind_engine(self)
            prepared.append(toolbox)
        return prepared

    def _prepare_capabilities(self, names: Iterable[str]) -> list[Capability]:
        prepared: list[Capability] = []
        for name in names:
            capability = create_capability(name)
            capability.bind(self)
            prepared.append(capability)
        return prepared

    def _prepare_core_participants(self) -> list[object]:
        attachment_service = AttachmentIngestionService(knowledge_hub=self.knowledge_hub, session=self.session)
        participants = [AttachmentIngressParticipant(attachment_service)]
        for participant in participants:
            bind = getattr(participant, "bind", None)
            if bind is not None:
                bind(self)
        return participants

    def _register(self, spec: ActionSpec) -> None:
        self.action_registry[spec.action_id] = spec

    def _register_toolboxes(self) -> None:
        for toolbox in self.toolboxes:
            specs = list(toolbox.action_specs())
            self.tool_index.register_toolbox_actions(toolbox.toolbox_name, specs)
            for spec in specs:
                self._register(spec)

    def _register_capabilities(self) -> None:
        for capability in self.capabilities:
            for spec in capability.action_specs():
                self._register(spec)

    def _register_core_actions(self) -> None:
        self._register(
            ActionSpec(
                "engine.inspect_skill",
                "Inspect skill",
                "Load the full SKILL.md for a reachable skill.",
                {"type": "object", "properties": {"skill": {"type": "string"}}, "required": ["skill"]},
                lambda args: self.inspect_skill(args["skill"]),
                "runtime.engine",
            )
        )
        self._register(
            ActionSpec(
                "engine.inspect_action",
                "Inspect action",
                "Inspect an action description and input schema.",
                {"type": "object", "properties": {"action": {"type": "string"}}, "required": ["action"]},
                lambda args: self.inspect_action(args["action"]),
                "runtime.engine",
            )
        )
        self._register(
            ActionSpec(
                "engine.enter_skill",
                "Enter skill",
                "Switch the active skill.",
                {"type": "object", "properties": {"skill": {"type": "string"}}, "required": ["skill"]},
                lambda args: self.enter_skill(args["skill"]),
                "runtime.engine",
            )
        )
        self._register(
            ActionSpec(
                "engine.list_child_skills",
                "List child skills",
                "List direct child skills for the active skill.",
                {"type": "object", "properties": {}},
                lambda args: self.list_child_skills(),
                "runtime.engine",
            )
        )

    def inspect_skill(self, skill: str) -> str:
        target = self.skill_runtime.resolve_skill_alias(skill)
        return self.registry.get_skill(target).markdown_path.read_text(encoding="utf-8")

    def inspect_action(self, action: str) -> str:
        spec = self.action_registry[action]
        return json.dumps(
            {
                "action": spec.action_id,
                "title": spec.title,
                "description": spec.description,
                "input_schema": spec.input_schema,
                "source": spec.source,
                "detail": spec.detail,
            },
            ensure_ascii=False,
            indent=2,
        )

    def list_child_skills(self) -> str:
        rows = self.registry.list_children_cards(self.skill_runtime.active_skill_id)
        return json.dumps([{"skill": skill_id, "summary": summary} for skill_id, summary in rows], ensure_ascii=False, indent=2)

    def enter_skill(self, skill: str) -> str:
        result = self.skill_runtime.enter_skill(skill)
        self.context.active_skill_id = self.skill_runtime.active_skill_id
        self.events.emit("skill.entered", skill=self.skill_runtime.active_skill_id)
        return result

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

    def has_visible_wiki_actions(self, surface_snapshot) -> bool:  # noqa: ANN001
        return any(spec.action_id.startswith("wiki.") for spec in surface_snapshot.visible_actions)

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
    ):
        target_skill = self.skill_runtime.active_skill_id if skill in (None, "", "root") else self.skill_runtime.resolve_skill_alias(skill)
        child_task_id = f"{self.settings.task_id}__{role_name}"
        return Engine(
            skill_root=target_skill,
            provider=self.provider,
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            user_id=self.settings.user_id,
            conversation_id=self.settings.conversation_id,
            task_id=child_task_id,
            toolboxes=[toolbox.toolbox_name for toolbox in self.toolboxes],
            enhancements=enhancements,
            storage_base=self.session.paths.root.parents[2],
            role_name=role_name,
            persistent_worker=persistent_worker,
            registry=self.registry,
            agent_spec=AgentSpec(
                name=role_name,
                root_skill=target_skill,
                toolboxes=[toolbox.toolbox_name for toolbox in self.toolboxes],
                capabilities=enhancements,
                llm={"provider": self.provider, "model": self.model, "api_key": self.api_key, "base_url": self.base_url},
                context_policy={"max_prompt_chars": self.settings.max_prompt_chars},
            ),
            context_policy={"max_prompt_chars": self.settings.max_prompt_chars},
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
    payload = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    payload["source_path"] = str(spec_path.as_posix())
    return AgentSpec.from_mapping(payload)
