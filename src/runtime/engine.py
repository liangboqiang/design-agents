from __future__ import annotations

from .builder import EngineRuntimeBundle


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
        self.service_hub = bundle.service_hub
        self.wiki_hub = bundle.knowledge_hub
        self.skill_state = bundle.skill_state
        self.tool_index = bundle.tool_index
        self.toolbox_hub = bundle.toolbox_hub
        self.surface_resolver = bundle.surface_resolver
        self.surface_assembler = bundle.surface_assembler
        self.prompt_assembler = bundle.prompt_assembler
        self.reply_parser = bundle.reply_parser
        self.normalizer = bundle.normalizer
        self.audit = bundle.audit
        self.events = bundle.events
        self.runtime_state = bundle.runtime_state
        self.action_registry = bundle.action_registry
        self.toolboxes = bundle.toolboxes
        self.capabilities = bundle.capabilities
        self.participants = bundle.participants
        self.participant_set = None
        self.lifecycle = bundle.lifecycle
        self.dispatcher = bundle.dispatcher
        self.harness_ports = None
        self.harness = None
        self.control = None
        self.child_factory = None
        self.failure_sink = bundle.failure_sink
        self.fault_boundary = bundle.fault_boundary

    def chat(self, message: str, files: list[dict] | None = None) -> str:
        return self.harness.chat(message, files=files)

    def tick(self) -> str:
        autonomy = next(
            (capability for capability in self.capabilities if capability.capability_name == "autonomy"),
            None,
        )
        if autonomy is None:
            return "Autonomy not enabled."
        result = autonomy.idle_tick()
        if result and not result.startswith("No unclaimed"):
            return self.chat(f"Auto-claimed task detail:\n{result}")
        return result

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
