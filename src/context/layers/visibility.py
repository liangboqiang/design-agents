from __future__ import annotations

from schemas.runtime import SurfaceSnapshot


def summarize_surface(snapshot: SurfaceSnapshot) -> tuple[list[tuple[str, str]], list[str]]:
    skill_cards = snapshot.visible_skills
    action_lines = [f"- {action.action_id}: {action.description} | source={action.source}" for action in snapshot.visible_actions]
    return skill_cards, action_lines
