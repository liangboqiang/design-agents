from __future__ import annotations

from schemas.action import ActionSpec
from schemas.runtime import SurfaceSnapshot

from governance.boundary import CORE_ENGINE_ACTIONS
from governance.dedupe import dedupe_actions, dedupe_pairs


class SurfaceResolver:
    def __init__(self, registry, activation_policy, audit):  # noqa: ANN001
        self.registry = registry
        self.activation_policy = activation_policy
        self.audit = audit

    def resolve(
        self,
        *,
        skill_runtime,
        action_registry: dict[str, ActionSpec],
        state_fragments: list[str],
        recent_events: list,
    ) -> SurfaceSnapshot:
        base_skill_ids = skill_runtime.base_skill_ids()
        activated_skill_ids, governance_notes = self.activation_policy.resolve(
            active_skill_id=skill_runtime.active_skill_id,
            base_skill_ids=base_skill_ids,
            recent_events=recent_events,
            state_fragments=state_fragments,
        )

        actions: list[ActionSpec] = []
        for skill_id in activated_skill_ids:
            skill = self.registry.get_skill(skill_id)
            for action_id in skill.actions:
                if action_id in action_registry:
                    actions.append(action_registry[action_id])
        for action_id in CORE_ENGINE_ACTIONS:
            if action_id in action_registry:
                actions.append(action_registry[action_id])

        visible_actions = dedupe_actions(actions)
        visible_skills = dedupe_pairs(skill_runtime.visible_skill_cards(activated_skill_ids))
        visible_toolboxes = sorted({action.source for action in visible_actions})

        self.audit.record(
            "surface.resolve",
            active_skill=skill_runtime.active_skill_id,
            activated_skill_ids=activated_skill_ids,
            visible_actions=[action.action_id for action in visible_actions],
            visible_toolboxes=visible_toolboxes,
        )

        return SurfaceSnapshot(
            visible_actions=visible_actions,
            visible_skills=visible_skills,
            visible_toolboxes=visible_toolboxes,
            activated_skill_ids=activated_skill_ids,
            governance_notes=governance_notes,
        )
