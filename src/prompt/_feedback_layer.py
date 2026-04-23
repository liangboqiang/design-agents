from __future__ import annotations


class FeedbackLayer:
    def build(self, recent_events, audit) -> list[tuple[str, str]]:  # noqa: ANN001
        event_body = "\n".join(
            f"- {event.name}: {event.payload}"
            for event in recent_events[-8:]
        ) or "- (none)"
        audit_body = "\n".join(
            f"- {entry.decision}: {entry.payload}"
            for entry in audit.recent(8)
        ) or "- (none)"
        return [
            ("Recent Events", event_body),
            ("Governance Audit", audit_body),
        ]

