from __future__ import annotations


class SkillRuntime:
    def __init__(self, registry, root_skill_id: str, audit):  # noqa: ANN001
        self.registry = registry
        self.root_skill_id = root_skill_id
        self.active_skill_id = root_skill_id
        self.audit = audit

    def active_skill(self):
        return self.registry.get_skill(self.active_skill_id)

    def base_skill_ids(self) -> list[str]:
        return self.registry.refs_resolver.resolve(self.active_skill_id)

    def activated_skill_ids(self) -> list[str]:
        return self.base_skill_ids()

    def visible_skill_cards(self, activated_skill_ids: list[str]) -> list[tuple[str, str]]:
        rows = list(self.registry.list_children_cards(self.active_skill_id))
        for skill_id in activated_skill_ids:
            if skill_id == self.active_skill_id:
                continue
            skill = self.registry.get_skill(skill_id)
            rows.append((skill_id, skill.description or skill.name))
        return rows

    def resolve_skill_alias(self, raw_skill: str) -> str:
        raw_skill = raw_skill.strip()
        if raw_skill in {"root", self.root_skill_id, self.active_skill_id}:
            return self.root_skill_id if raw_skill == "root" else raw_skill
        if raw_skill in self.registry.skills:
            return raw_skill
        active = self.active_skill()
        for candidate in [*active.children, *active.refs]:
            skill = self.registry.get_skill(candidate)
            if candidate.endswith(raw_skill) or skill.name == raw_skill:
                return candidate
        raise ValueError(f"Skill not reachable from current scope: {raw_skill}")

    def enter_skill(self, raw_skill: str) -> str:
        target = self.resolve_skill_alias(raw_skill)
        self.active_skill_id = target
        self.audit.record("skill.enter", target=target)
        skill = self.registry.get_skill(target)
        return f"Entered skill {target}: {skill.description or skill.name}"

