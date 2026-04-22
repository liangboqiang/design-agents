from __future__ import annotations

from shared.text import clip_text

from .dedupe import dedupe_strings


class Normalizer:
    def normalize_tool_result(self, action_id: str, result: str, *, limit: int = 4000) -> str:
        return clip_text(result, limit=limit)

    def normalize_state_fragments(self, fragments: list[str]) -> list[str]:
        return dedupe_strings([fragment.strip() for fragment in fragments if fragment.strip()])

    def normalize_sections(self, sections: list[tuple[str, str]]) -> list[tuple[str, str]]:
        normalized: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for title, body in sections:
            key = (title.strip(), body.strip())
            if key in seen or not key[1]:
                continue
            seen.add(key)
            normalized.append(key)
        return normalized
