from __future__ import annotations

from textwrap import dedent

from .models import ActionSpec, EngineContext
from .skill_loader import SkillCatalog


class PromptBuilder:
    def __init__(self, catalog: SkillCatalog):
        self.catalog = catalog

    def build_system_prompt(
        self,
        context: EngineContext,
        visible_actions: list[ActionSpec],
        state_fragments: list[str],
    ) -> str:
        active = self.catalog.get(context.active_skill_id)
        child_lines = "\n".join(
            f"- {skill_id}: {summary}"
            for skill_id, summary in self.catalog.list_children_cards(context.active_skill_id)
        ) or "- (none)"
        action_lines = "\n".join(
            f"- {a.action_id}: {a.description} | source={a.source}"
            for a in visible_actions
        ) or "- (none)"
        state_block = "\n".join(state_fragments) if state_fragments else "(no extra state)"
        return dedent(
            f"""
            You are an instantiated skill engine.

            ## Identity
            - engine_id: {context.engine_id}
            - root_skill: {context.root_skill_id}
            - active_skill: {context.active_skill_id}
            - provider: {context.settings.provider}
            - model: {context.settings.model}
            - base_url: {context.settings.base_url or '(provider default)'}

            ## Active Skill Summary
            - title: {active.name}
            - description: {active.description or 'No description'}

            ## Child Skills Available
            {child_lines}

            ## Visible Actions
            {action_lines}

            ## State Fragments
            {state_block}

            ## Response Contract
            Return strict JSON only:
            {{
              "assistant_message": "string",
              "tool_calls": [{{"action": "action.id", "arguments": {{}}}}]
            }}

            Rules:
            1. If you need more detail, inspect skill/action first.
            2. Only call visible actions.
            3. Use engine.enter_skill when a child skill is more suitable.
            4. Keep assistant_message concise before tool use.
            """
        ).strip()

    def build_messages(self, history: list[dict], keep_turns: int) -> list[dict]:
        rows = history[-keep_turns:] if keep_turns > 0 else history
        messages: list[dict] = []
        for item in rows:
            role = item["role"]
            content = item["content"]
            if role == "tool":
                messages.append(
                    {
                        "role": "user",
                        "content": f"<tool_result action=\"{item['action']}\">\n{content}\n</tool_result>",
                    }
                )
            elif role == "system":
                messages.append(
                    {
                        "role": "user",
                        "content": f"<engine_note>\n{content}\n</engine_note>",
                    }
                )
            else:
                messages.append({"role": role, "content": content})
        return messages
