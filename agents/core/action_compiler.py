from __future__ import annotations

from collections import OrderedDict

from .models import ActionSpec
from .skill_loader import SkillCatalog


class ActionCompiler:
    def __init__(self, catalog: SkillCatalog):
        self.catalog = catalog

    def compile_visible_actions(self, active_skill_id: str, registry: dict[str, ActionSpec]) -> list[ActionSpec]:
        ordered: "OrderedDict[str, ActionSpec]" = OrderedDict()
        for skill_id in self.catalog.closure_for_active_skill(active_skill_id):
            node = self.catalog.get(skill_id)
            for action_id in node.actions:
                if action_id in registry and action_id not in ordered:
                    ordered[action_id] = registry[action_id]
        for reserved in ("engine.inspect_skill", "engine.inspect_action", "engine.enter_skill", "engine.list_child_skills"):
            if reserved in registry and reserved not in ordered:
                ordered[reserved] = registry[reserved]
        return list(ordered.values())
