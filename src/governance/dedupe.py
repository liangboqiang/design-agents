from __future__ import annotations

from schemas.action import ActionSpec


def dedupe_actions(actions: list[ActionSpec]) -> list[ActionSpec]:
    ordered: dict[str, ActionSpec] = {}
    for action in actions:
        if action.action_id not in ordered:
            ordered[action.action_id] = action
    return list(ordered.values())


def dedupe_pairs(rows: list[tuple[str, str]]) -> list[tuple[str, str]]:
    ordered: dict[str, tuple[str, str]] = {}
    for key, value in rows:
        if key not in ordered:
            ordered[key] = (key, value)
    return list(ordered.values())


def dedupe_strings(rows: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for row in rows:
        if row not in seen:
            seen.add(row)
            ordered.append(row)
    return ordered

