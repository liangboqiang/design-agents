from __future__ import annotations


class IdentityLayer:
    def build(self, engine_context, skill_runtime) -> tuple[str, str]:  # noqa: ANN001
        active = skill_runtime.active_skill()
        body = "\n".join(
            [
                f"- agent_name: {engine_context.agent_name}",
                f"- engine_id: {engine_context.engine_id}",
                f"- root_skill: {engine_context.root_skill_id}",
                f"- active_skill: {engine_context.active_skill_id}",
                f"- provider: {engine_context.settings.provider}",
                f"- model: {engine_context.settings.model}",
                f"- base_url: {engine_context.settings.base_url or '(none)'}",
                f"- active_skill_title: {active.name}",
                f"- active_skill_description: {active.description or 'No description'}",
            ]
        )
        return ("Identity", body)

