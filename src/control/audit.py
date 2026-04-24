from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any


@dataclass(slots=True)
class AuditEntry:
    decision: str
    payload: dict[str, Any]
    ts: float = field(default_factory=time)


class GovernanceAudit:
    def __init__(self):
        self.entries: list[AuditEntry] = []

    def record(self, decision: str, **payload) -> None:
        self.entries.append(AuditEntry(decision=decision, payload=payload))

    def recent(self, limit: int = 10) -> list[AuditEntry]:
        return self.entries[-limit:]

    def snapshot(self) -> list[dict]:
        return [
            {"decision": entry.decision, "payload": entry.payload, "ts": entry.ts}
            for entry in self.entries
        ]
