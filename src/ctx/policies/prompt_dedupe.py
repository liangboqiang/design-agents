from __future__ import annotations


def dedupe_sections(sections: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    ordered: list[tuple[str, str]] = []
    for section in sections:
        if section not in seen and section[1].strip():
            seen.add(section)
            ordered.append(section)
    return ordered

