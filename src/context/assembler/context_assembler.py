from __future__ import annotations

from pathlib import Path

from context.indexes.context_index import ContextIndex
from context.policies.prompt_budget import apply_prompt_budget
from context.policies.prompt_dedupe import dedupe_sections
from governance.normalizer import Normalizer

from .expansion_layer import ExpansionLayer
from .feedback_layer import FeedbackLayer
from .identity_layer import IdentityLayer
from .state_layer import StateLayer
from .surface_layer import SurfaceLayer


class ContextAssembler:
    def __init__(self, templates_dir: Path, *, max_prompt_chars: int = 18_000):
        self.index = ContextIndex(templates_dir)
        self.max_prompt_chars = max_prompt_chars
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
        skill_runtime,
        surface_snapshot,
        history_rows: list[dict],
        state_fragments: list[str],
        recent_events: list,
        audit,
        registry,
        knowledge_brief: str | None = None,
        knowledge_actions_visible: bool = False,
    ) -> str:
        sections = [self.identity_layer.build(engine_context, skill_runtime)]
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
        sections = apply_prompt_budget(sections, limit=self.max_prompt_chars)
        sections.append(("Response Contract", self._response_contract(knowledge_actions_visible)))
        template = self._template("system_prompt.md")
        rendered_sections = "\n\n".join(f"## {title}\n{body}" for title, body in sections)
        return template.replace("{{sections}}", rendered_sections).strip()

    def build_messages(self, history: list[dict], keep_turns: int) -> list[dict]:
        rows = history[-keep_turns:] if keep_turns > 0 else history
        messages: list[dict] = []
        for item in rows:
            role = item["role"]
            content = item["content"]
            if role == "tool":
                template = self._template("tool_result.md")
                body = template.replace("{{action}}", item["action"]).replace("{{content}}", content)
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

    def _template(self, name: str) -> str:
        if name in self.index.assets:
            return self.index.get(name).read_text(encoding="utf-8")
        if name == "tool_result.md":
            return '<tool_result action="{{action}}">\n{{content}}\n</tool_result>'
        if name == "compact_summary.md":
            return "[COMPACTED SUMMARY]\n{{summary}}"
        return "You are a governed skill runtime.\n\n{{sections}}"
