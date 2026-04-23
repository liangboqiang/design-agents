from __future__ import annotations

from ._visibility_policy import summarize_surface


class SurfaceLayer:
    def build(self, surface_snapshot) -> list[tuple[str, str]]:  # noqa: ANN001
        skill_cards, action_lines = summarize_surface(surface_snapshot)
        skills_body = "\n".join(f"- {skill_id}: {summary}" for skill_id, summary in skill_cards) or "- (none)"
        actions_body = "\n".join(action_lines) or "- (none)"
        toolboxes_body = "\n".join(f"- {name}" for name in surface_snapshot.visible_toolboxes) or "- (none)"
        return [
            ("Visible Skills", skills_body),
            ("Visible Actions", actions_body),
            ("Visible Toolboxes", toolboxes_body),
        ]
