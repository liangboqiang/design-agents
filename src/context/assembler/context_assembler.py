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
        wiki_hub=None,
    ) -> str:
        sections = [self.identity_layer.build(engine_context, skill_runtime)]
        sections.extend(self.surface_layer.build(surface_snapshot))
        sections.extend(self.state_layer.build(history_rows, self.normalizer.normalize_state_fragments(state_fragments)))
        sections.extend(self.expansion_layer.build(surface_snapshot, registry))
        sections.extend(self.feedback_layer.build(recent_events, audit))
        if wiki_hub is not None:
            sections.append(
                (
                    "Knowledge Hub",
                    (
                        "The LLM Wiki is the canonical knowledge center.\n"
                        "Never treat raw source files, SKILL.md files, tool code, or user attachments as final truth if the wiki already has compiled pages.\n"
                        "Use wiki.refresh when system/business/user sources may have changed.\n"
                        "Use wiki.search / wiki.read_page / wiki.answer before asking the user to restate known information.\n\n"
                        f"{wiki_hub.system_brief()}"
                    ),
                )
            )
        sections = self.normalizer.normalize_sections(sections)
        sections = dedupe_sections(sections)
        sections = apply_prompt_budget(sections, limit=self.max_prompt_chars)
        rules = (
            "Return strict JSON only:\n"
            '{\n  "assistant_message": "string",\n  "tool_calls": [{"action": "action.id", "arguments": {}}]\n}\n'
            "Rules:\n"
            "1. If knowledge is needed, prefer wiki actions first.\n"
            "2. Only call visible actions.\n"
            "3. Use engine.enter_skill when another child skill is more suitable.\n"
            "4. Keep assistant_message concise before tool use."
        )
        sections.append(("Response Contract", rules))
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

    def _template(self, name: str) -> str:
        if name in self.index.assets:
            return self.index.get(name).read_text(encoding="utf-8")
        if name == "tool_result.md":
            return '<tool_result action="{{action}}">\n{{content}}\n</tool_result>'
        if name == "compact_summary.md":
            return "[COMPACTED SUMMARY]\n{{summary}}"
        return "You are a governed skill runtime.\n\n{{sections}}"
