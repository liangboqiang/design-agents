from __future__ import annotations

from control.normalizer import Normalizer

from .budget import apply_context_budget
from .dedupe import dedupe_sections
from .layers.expansion import ExpansionLayer
from .layers.feedback import FeedbackLayer
from .layers.identity import IdentityLayer
from .layers.state import StateLayer
from .layers.surface import SurfaceLayer


SYSTEM_HEADER = "You are a governed runtime operating inside the design-agents control plane."
TOOL_RESULT_ENVELOPE = '<tool_result action="{action}">\n{content}\n</tool_result>'


class ContextAssembler:
    """Builds model-facing context from runtime state, agent page context, and visible surface.

    The context package is an engineering layer. It does not scan editable template
    assets. Agent-specific instructions live directly in agent/page.md under the
    `## Context` section; stable envelopes and contracts remain protocol constants.
    """

    def __init__(self, *, max_prompt_chars: int = 18_000):
        self.max_prompt_chars = int(max_prompt_chars)
        self.identity_layer = IdentityLayer()
        self.surface_layer = SurfaceLayer()
        self.state_layer = StateLayer()
        self.expansion_layer = ExpansionLayer()
        self.feedback_layer = FeedbackLayer()
        self.normalizer = Normalizer()

    def build_system_prompt(
        self,
        *,
        engine_context,
        skill_state,
        surface_snapshot,
        history_rows: list[dict],
        state_fragments: list[str],
        recent_events: list,
        audit,
        registry,
        knowledge_brief: str | None = None,
        knowledge_actions_visible: bool = False,
    ) -> str:
        sections: list[tuple[str, str]] = [self.identity_layer.build(engine_context, skill_state)]

        agent_context = str(getattr(engine_context, "agent_context", "") or "").strip()
        if agent_context:
            sections.append(("Agent Context", agent_context))

        sections.extend(self.surface_layer.build(surface_snapshot))
        sections.extend(self.state_layer.build(history_rows, self.normalizer.normalize_state_fragments(state_fragments)))
        sections.extend(self.expansion_layer.build(surface_snapshot, registry))
        sections.extend(self.feedback_layer.build(recent_events, audit))

        if knowledge_brief:
            sections.append(
                (
                    "Knowledge Hub",
                    (
                        "The LLM Wiki is the canonical knowledge center when wiki actions are explicitly visible.\n"
                        "Prefer compiled wiki pages over raw source files when both are available.\n"
                        "Do not infer hidden tools or hidden toolboxes.\n\n"
                        f"{knowledge_brief}"
                    ),
                )
            )

        sections = self.normalizer.normalize_sections(sections)
        sections = dedupe_sections(sections)
        sections = apply_context_budget(sections, limit=self.max_prompt_chars)
        sections.append(("Response Contract", self._response_contract(knowledge_actions_visible)))
        rendered_sections = "\n\n".join(f"## {title}\n{body}" for title, body in sections if str(body).strip())
        return f"{SYSTEM_HEADER}\n\n{rendered_sections}".strip()

    def build_messages(self, history: list[dict], keep_turns: int) -> list[dict]:
        rows = history[-keep_turns:] if keep_turns > 0 else history
        messages: list[dict] = []
        for item in rows:
            role = item["role"]
            content = item["content"]
            if role == "tool":
                body = TOOL_RESULT_ENVELOPE.format(action=item["action"], content=content)
                messages.append({"role": "user", "content": body})
                continue
            if role == "system":
                messages.append({"role": "user", "content": f"<system_note>\n{content}\n</system_note>"})
                continue
            if role == "user" and item.get("files"):
                file_block = "\n".join(
                    f'- name="{row.get("name", "")}" url="{row.get("url", "")}"'
                    for row in item["files"]
                )
                content = f"{content}\n\n<attachments>\n{file_block}\n</attachments>"
            messages.append({"role": role, "content": content})
        return messages

    def _response_contract(self, knowledge_actions_visible: bool) -> str:
        rules = [
            "Return strict JSON only:",
            '{\n  "assistant_message": "string",\n  "tool_calls": [{"action": "action.id", "arguments": {}}]\n}',
            "Rules:",
        ]
        if knowledge_actions_visible:
            rules.append("1. If knowledge is needed, prefer visible wiki actions before asking the user to restate known information.")
            offset = 2
        else:
            offset = 1
        rules.extend(
            [
                f"{offset}. Only call visible actions.",
                f"{offset + 1}. Use engine.enter_skill when another child skill is more suitable.",
                f"{offset + 2}. Keep assistant_message concise before tool use.",
                f"{offset + 3}. Never assume hidden tools, hidden refs, or hidden toolboxes exist.",
            ]
        )
        return "\n".join(rules)


# Compatibility alias for older names inside local experiments.
PromptAssembler = ContextAssembler
