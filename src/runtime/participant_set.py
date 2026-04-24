from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class AttachmentIngressParticipant:
    """Lifecycle participant that owns attachment intake.

    It converts raw user attachments into explicit runtime state and an optional
    system note, keeping TurnDriver free of knowledge-specific branching.
    """

    participant_name = "attachment_ingress"

    def __init__(self, service):  # noqa: ANN001
        self.service = service
        self.engine = None

    def bind(self, engine) -> None:  # noqa: ANN001
        self.engine = engine

    def before_user_turn(self, message: str, files: list[dict[str, Any]] | None = None) -> None:
        if self.engine is None:
            raise RuntimeError("AttachmentIngressParticipant is not bound to an engine.")
        result = self.service.ingest(files)
        if not result:
            return
        self.engine.session.history.append_system(f"Attachment ingest summary:\n{result}")
        snapshot = self.service.latest_snapshot()
        self.engine.events.emit(
            "attachments.ingested",
            message=message,
            count=snapshot.get("file_count", 0),
            files=snapshot.get("file_names", []),
        )

    def before_model_call(self) -> None:
        return None

    def after_tool_call(self, action_id: str, result: str) -> None:
        return None

    def state_fragments(self) -> list[str]:
        return self.service.state_fragments()


@dataclass(slots=True)
class ParticipantSet:
    core: list[object] = field(default_factory=list)

    def all(self) -> list[object]:
        return list(self.core)
