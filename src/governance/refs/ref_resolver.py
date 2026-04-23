from __future__ import annotations

from schemas.skill import SkillSpec


class RefResolver:
    def __init__(self, skills: dict[str, SkillSpec]):
        self.skills = skills

    def resolve(self, skill_id: str) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []

        def visit(current_id: str) -> None:
            if current_id in seen or current_id not in self.skills:
                return
            seen.add(current_id)
            ordered.append(current_id)
            for ref_id in self.skills[current_id].refs:
                visit(ref_id)

        visit(skill_id)
        return ordered


RefsResolver = RefResolver
