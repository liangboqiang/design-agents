from __future__ import annotations

from pathlib import Path

from schemas.agent import AgentSpec


class ChildFactory:
    """Build child engines from a parent engine using inherited runtime config.

    This factory is governance-oriented: a child engine should inherit the
    parent's execution environment while defaulting to a smaller prompt budget
    and a narrower task description.
    """

    def __init__(
        self,
        *,
        storage_base: Path | None = None,
        prompt_shrink_ratio: float = 0.5,
        min_prompt_chars: int = 6000,
    ):
        self.storage_base = storage_base
        self.prompt_shrink_ratio = float(prompt_shrink_ratio)
        self.min_prompt_chars = int(min_prompt_chars)

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
        target_skill = (
            parent.skill_state.active_skill_id
            if skill in (None, "", "root")
            else parent.skill_state.resolve_skill_alias(skill)
        )
        child_task_id = f"{parent.settings.task_id}__{role_name}"
        storage_base = self.storage_base or parent.session.paths.root.parents[2]
        child_toolboxes = list(
            toolboxes if toolboxes is not None else [toolbox.toolbox_name for toolbox in parent.toolboxes]
        )

        child_prompt_chars = self._derive_prompt_budget(parent.settings.max_prompt_chars)
        child_context_policy = dict(parent.agent_spec.context_policy or {})
        child_context_policy["max_prompt_chars"] = child_prompt_chars

        parent_name = getattr(parent.agent_spec, "name", "") or parent.engine_id
        spec = AgentSpec(
            name=role_name,
            root_skill=target_skill,
            description=f"Child agent built by {parent_name} for role {role_name}.",
            toolboxes=child_toolboxes,
            capabilities=list(enhancements),
            llm={
                "provider": parent.provider,
                "model": parent.model,
                "api_key": parent.api_key,
                "base_url": parent.base_url,
            },
            context_policy=child_context_policy,
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

    def _derive_prompt_budget(self, parent_budget: int) -> int:
        parent_budget = max(1, int(parent_budget))
        shrunk = int(parent_budget * self.prompt_shrink_ratio)
        shrunk = max(self.min_prompt_chars, shrunk)
        return min(parent_budget, shrunk)
