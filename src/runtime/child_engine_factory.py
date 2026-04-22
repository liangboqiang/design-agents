from __future__ import annotations

from pathlib import Path

from schemas.agent import AgentSpec


class ChildEngineFactory:
    def __init__(self, *, storage_base: Path | None = None):
        self.storage_base = storage_base

    def spawn_from_parent(
        self,
        parent,
        *,
        skill: str | None,
        enhancements: list[str],
        role_name: str,
        persistent_worker: bool = False,
        toolboxes: list[str] | None = None,
    ):
        target_skill = parent.skill_runtime.active_skill_id if skill in (None, "", "root") else parent.skill_runtime.resolve_skill_alias(skill)
        child_task_id = f"{parent.settings.task_id}__{role_name}"
        storage_base = self.storage_base or parent.session.paths.root.parents[2]
        child_toolboxes = list(toolboxes if toolboxes is not None else [toolbox.toolbox_name for toolbox in parent.toolboxes])
        spec = AgentSpec(
            name=role_name,
            root_skill=target_skill,
            toolboxes=child_toolboxes,
            capabilities=list(enhancements),
            llm={
                "provider": parent.provider,
                "model": parent.model,
                "api_key": parent.api_key,
                "base_url": parent.base_url,
            },
            context_policy={"max_prompt_chars": parent.settings.max_prompt_chars},
        )
        return parent.__class__.from_agent_spec(
            spec,
            user_id=parent.settings.user_id,
            conversation_id=parent.settings.conversation_id,
            task_id=child_task_id,
            role_name=role_name,
            persistent_worker=persistent_worker,
            registry=parent.registry,
            storage_base=Path(storage_base),
        )
