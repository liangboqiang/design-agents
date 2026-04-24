from __future__ import annotations

from shared.text import clip_text


def apply_context_budget(sections: list[tuple[str, str]], *, limit: int) -> list[tuple[str, str]]:
    if limit <= 0:
        return sections
    total = 0
    budgeted: list[tuple[str, str]] = []
    for title, body in sections:
        header = f"## {title}\n"
        remaining = limit - total - len(header)
        if remaining <= 0:
            break
        clipped = clip_text(body, limit=remaining)
        budgeted.append((title, clipped))
        total += len(header) + len(clipped)
    return budgeted

# Backward-compatible function name inside the context package.
apply_prompt_budget = apply_context_budget
