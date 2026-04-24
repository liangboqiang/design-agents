from __future__ import annotations


class ExpansionLayer:
    def build(self, surface_snapshot, registry) -> list[tuple[str, str]]:  # noqa: ANN001
        if not surface_snapshot.activated_skill_ids:
            return [("Expansion", "(no activated refs or governance additions)")]
        rows = []
        for skill_id in surface_snapshot.activated_skill_ids:
            skill = registry.get_skill(skill_id)
            rows.append(f"- {skill_id}: {skill.description or skill.name}")
        notes = "\n".join(f"- {note}" for note in surface_snapshot.governance_notes) or "- (none)"
        return [
            ("Expansion", "\n".join(rows)),
            ("Governance Notes", notes),
        ]
