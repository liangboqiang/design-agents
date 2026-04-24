from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class KnowledgeSelection:
    brief: str | None
    actions_visible: bool


class KnowledgePicker:
    def pick(self, *, surface_snapshot, knowledge_hub) -> KnowledgeSelection:  # noqa: ANN001
        actions_visible = any(spec.action_id.startswith("wiki.") for spec in surface_snapshot.visible_actions)
        brief = knowledge_hub.system_brief() if actions_visible else None
        return KnowledgeSelection(brief=brief, actions_visible=actions_visible)
