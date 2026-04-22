from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Iterable

from agents.capabilities.base import Capability
from agents.capabilities.registry import create_capability
from agents.core.action_compiler import ActionCompiler
from agents.core.dispatcher import ExecutorDispatcher
from agents.core.history import HistoryStore
from agents.core.models import ActionSpec, EngineContext, EngineSettings
from agents.core.prompt_builder import PromptBuilder
from agents.core.response_parser import ResponseParser
from agents.core.skill_loader import SkillCatalog
from agents.core.storage import JsonStore, ensure_runtime_paths
from agents.llm.config import resolve_llm_config
from agents.llm.factory import LLMFactory
from agents.toolboxes.base import Toolbox
from agents.toolboxes.files import FileToolbox
from agents.toolboxes.shell import ShellToolbox


class Engine:
    def __init__(
        self,
        skill_root: Path,
        provider: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        *,
        user_id: str = "default_user",
        conversation_id: str = "default_conversation",
        task_id: str = "default_task",
        toolboxes: list[Toolbox] | None = None,
        enhancements: list[str] | None = None,
        storage_base: Path | None = None,
        max_steps: int = 12,
        role_name: str | None = None,
        persistent_worker: bool = False,
    ):
        llm_config = resolve_llm_config(provider, model, api_key, base_url)

        self.skill_root = self._resolve_skill_root(Path(skill_root))
        self.skill_space_root = self._detect_skill_space_root(self.skill_root)
        self.provider = llm_config.provider
        self.model = llm_config.model
        self.api_key = llm_config.api_key
        self.base_url = llm_config.base_url
        self.enhancement_names = [item.strip() for item in (enhancements or [])]
        self.engine_id = role_name or f"engine-{str(uuid.uuid4())[:8]}"
        self.persistent_worker = persistent_worker
        self.settings = EngineSettings(
            self.provider,
            self.model,
            self.api_key,
            self.base_url,
            user_id,
            conversation_id,
            task_id,
            max_steps=max_steps,
        )

        storage_root = (storage_base or Path(".runtime_data")).resolve()
        self.paths = ensure_runtime_paths(storage_root, user_id, conversation_id, task_id)
        self.workspace_root = (self.paths.root / "workspace_root").resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.history = HistoryStore(self.paths.history_dir)
        self.catalog = SkillCatalog(self.skill_space_root)
        self.root_skill_id = self.catalog._skill_id_for(self.skill_root)
        if self.root_skill_id not in self.catalog.skills:
            raise ValueError(
                f"Skill root '{self.skill_root}' was not loaded from skill space "
                f"'{self.skill_space_root}'."
            )

        self.active_skill_id = self.root_skill_id
        self.context = EngineContext(
            self.engine_id,
            self.root_skill_id,
            self.active_skill_id,
            self.settings,
            self.paths,
        )
        self.llm = LLMFactory.create(self.provider, self.model, self.api_key, self.base_url)
        requested_toolboxes = toolboxes or [FileToolbox(), ShellToolbox()]
        self.toolboxes = self._prepare_toolboxes(requested_toolboxes)
        self.capabilities: list[Capability] = []
        for name in self.enhancement_names:
            capability = create_capability(name)
            capability.bind(self)
            self.capabilities.append(capability)

        self.action_registry: dict[str, ActionSpec] = {}
        self._register_core_actions()
        self._register_toolboxes()
        self._register_capability_actions()
        self.action_compiler = ActionCompiler(self.catalog)
        self.prompt_builder = PromptBuilder(self.catalog)
        self.dispatcher = ExecutorDispatcher(self.action_registry)

    @staticmethod
    def _resolve_skill_root(skill_root: Path) -> Path:
        candidate = Path(skill_root)
        search_roots: list[Path] = []
        if candidate.is_absolute():
            search_roots.append(candidate)
        else:
            search_roots.append(candidate)
            search_roots.append(Path(__file__).resolve().parents[1] / candidate)

        for option in search_roots:
            resolved = option.resolve()
            if resolved.is_dir() and (resolved / "SKILL.md").exists():
                return resolved

        attempted = ", ".join(str(path.resolve()) for path in search_roots)
        raise FileNotFoundError(
            "Skill root must point to a directory containing SKILL.md. "
            f"Tried: {attempted}"
        )

    @staticmethod
    def _detect_skill_space_root(skill_root: Path) -> Path:
        current = skill_root.resolve()
        while current != current.parent:
            if (current / "core").exists() and (current / "domains").exists():
                return current
            current = current.parent
        return skill_root.parent

    def _prepare_toolboxes(self, toolboxes: Iterable[Toolbox]) -> list[Toolbox]:
        prepared: list[Toolbox] = []
        for toolbox in toolboxes:
            bound_root = toolbox.workspace_root.resolve() if toolbox.workspace_root else None
            if bound_root == self.workspace_root:
                prepared.append(toolbox)
            else:
                prepared.append(toolbox.spawn(self.workspace_root))
        return prepared

    def _register(self, spec: ActionSpec) -> None:
        self.action_registry[spec.action_id] = spec

    def _register_toolboxes(self) -> None:
        for toolbox in self.toolboxes:
            for spec in toolbox.action_specs():
                self._register(spec)

    def _register_capability_actions(self) -> None:
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
                "core.engine",
                "Use this when you need the exact skill body instead of the summary already in context.",
            )
        )
        self._register(
            ActionSpec(
                "engine.inspect_action",
                "Inspect action",
                "Inspect an action description and input schema.",
                {"type": "object", "properties": {"action": {"type": "string"}}, "required": ["action"]},
                lambda args: self.inspect_action(args["action"]),
                "core.engine",
            )
        )
        self._register(
            ActionSpec(
                "engine.enter_skill",
                "Enter skill",
                "Switch the active skill.",
                {"type": "object", "properties": {"skill": {"type": "string"}}, "required": ["skill"]},
                lambda args: self.enter_skill(args["skill"]),
                "core.engine",
            )
        )
        self._register(
            ActionSpec(
                "engine.list_child_skills",
                "List child skills",
                "List the direct child skills of the current skill.",
                {"type": "object", "properties": {}},
                lambda args: self.list_child_skills(),
                "core.engine",
            )
        )

    def capability(self, name: str):
        for capability in self.capabilities:
            if capability.capability_name == name:
                return capability
        return None

    def append_system_note(self, content: str) -> None:
        self.history.append_system(content)

    def append_tool_result(self, action: str, content: str) -> None:
        self.history.append_tool(action, content)

    def replace_history(self, rows: list[dict]) -> None:
        self.history.replace(rows)

    def read_history(self) -> list[dict]:
        return self.history.read()

    def _state_path(self, name: str) -> Path:
        target = (self.paths.state_dir / name).resolve()
        state_root = self.paths.state_dir.resolve()
        if not target.is_relative_to(state_root):
            raise ValueError(f"State path escapes state dir: {name}")
        return target

    def read_state_json(self, name: str, default: Any):
        return JsonStore(self._state_path(name)).read(default)

    def write_state_json(self, name: str, payload: Any) -> None:
        JsonStore(self._state_path(name)).write(payload)

    def inspect_skill(self, skill: str) -> str:
        target = self._resolve_skill_alias(skill)
        return self.catalog.get(target).markdown_path.read_text(encoding="utf-8")

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
        rows = self.catalog.list_children_cards(self.active_skill_id)
        return json.dumps(
            [{"skill": skill_id, "summary": summary} for skill_id, summary in rows],
            ensure_ascii=False,
            indent=2,
        )

    def _resolve_skill_alias(self, raw_skill: str) -> str:
        raw_skill = raw_skill.strip()
        if raw_skill in {"root", self.root_skill_id}:
            return self.root_skill_id
        if raw_skill in self.catalog.skills:
            return raw_skill
        active_node = self.catalog.get(self.active_skill_id)
        for candidate in [*active_node.children, *active_node.refs]:
            if candidate.endswith(raw_skill) or self.catalog.get(candidate).name == raw_skill:
                return candidate
        raise ValueError(f"Skill not reachable from current scope: {raw_skill}")

    def enter_skill(self, skill: str) -> str:
        target = self._resolve_skill_alias(skill)
        self.active_skill_id = target
        self.context.active_skill_id = target
        node = self.catalog.get(target)
        return f"Entered skill {target}: {node.description or node.name}"

    def _visible_actions(self) -> list[ActionSpec]:
        return self.action_compiler.compile_visible_actions(self.active_skill_id, self.action_registry)

    def _state_fragments(self) -> list[str]:
        fragments: list[str] = []
        for capability in self.capabilities:
            fragments.extend(capability.state_fragments())
        return fragments

    def chat(self, message: str) -> str:
        for capability in self.capabilities:
            capability.before_user_turn(message)

        self.history.append_user(message)
        final_answer = ""

        for _ in range(self.settings.max_steps):
            for capability in self.capabilities:
                capability.before_model_call()

            visible_actions = self._visible_actions()
            system_prompt = self.prompt_builder.build_system_prompt(
                self.context,
                visible_actions,
                self._state_fragments(),
            )
            messages = self.prompt_builder.build_messages(
                self.history.read(),
                self.settings.history_keep_turns,
            )

            raw = self.llm.complete(system_prompt, messages)
            parsed = ResponseParser.parse(raw)

            if parsed.assistant_message:
                self.history.append_assistant(parsed.assistant_message)
                final_answer = parsed.assistant_message

            if not parsed.tool_calls:
                return final_answer or ""

            for call in parsed.tool_calls:
                result = self.dispatcher.dispatch(call.action, call.arguments)
                self.append_tool_result(call.action, result)
                for capability in self.capabilities:
                    capability.after_tool_call(call.action, result)
                final_answer = result

        return final_answer or "Max steps reached."

    def spawn_child(
        self,
        *,
        skill: str | None,
        enhancements: list[str],
        role_name: str,
        persistent_worker: bool = False,
    ):
        target_skill_path = (
            self.skill_root
            if skill in (None, "", "root", self.root_skill_id)
            else self.catalog.get(self._resolve_skill_alias(skill)).directory
        )
        child_task_id = f"{self.settings.task_id}__{role_name}"
        storage_root = self.paths.root.parents[2]
        child_paths = ensure_runtime_paths(
            storage_root,
            self.settings.user_id,
            self.settings.conversation_id,
            child_task_id,
        )
        child_workspace_root = (child_paths.root / "workspace_root").resolve()
        child_workspace_root.mkdir(parents=True, exist_ok=True)

        return Engine(
            skill_root=target_skill_path,
            provider=self.provider,
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            user_id=self.settings.user_id,
            conversation_id=self.settings.conversation_id,
            task_id=child_task_id,
            toolboxes=[toolbox.spawn(child_workspace_root) for toolbox in self.toolboxes],
            enhancements=enhancements,
            storage_base=storage_root,
            role_name=role_name,
            persistent_worker=persistent_worker,
        )

    def process_autonomy_tick(self) -> str:
        autonomy = self.capability("autonomy")
        if autonomy is None:
            return "Autonomy not enabled."
        result = autonomy.idle_tick()
        if result and not result.startswith("No unclaimed"):
            return self.chat(f"Auto-claimed task detail:\n{result}")
        return result
