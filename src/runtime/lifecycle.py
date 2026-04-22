from __future__ import annotations


class LifecycleManager:
    def __init__(self, participants: list, fault_reporter=None):  # noqa: ANN001
        self.participants = participants
        self.fault_reporter = fault_reporter

    def before_user_turn(self, message: str, files: list[dict] | None = None) -> None:
        for participant in self.participants:
            hook = getattr(participant, "before_user_turn", None)
            if hook is None:
                continue
            try:
                try:
                    hook(message, files=files)
                except TypeError:
                    hook(message)
            except Exception as exc:  # noqa: BLE001
                self._report(
                    phase="lifecycle.before_user_turn",
                    participant=participant,
                    exc=exc,
                    context={"message": message, "attachments": len(files or [])},
                )

    def before_model_call(self) -> None:
        for participant in self.participants:
            hook = getattr(participant, "before_model_call", None)
            if hook is None:
                continue
            try:
                hook()
            except Exception as exc:  # noqa: BLE001
                self._report(
                    phase="lifecycle.before_model_call",
                    participant=participant,
                    exc=exc,
                )

    def after_tool_call(self, action_id: str, result: str) -> None:
        for participant in self.participants:
            hook = getattr(participant, "after_tool_call", None)
            if hook is None:
                continue
            try:
                hook(action_id, result)
            except Exception as exc:  # noqa: BLE001
                self._report(
                    phase="lifecycle.after_tool_call",
                    participant=participant,
                    exc=exc,
                    context={"action_id": action_id},
                )

    def state_fragments(self) -> list[str]:
        fragments: list[str] = []
        for participant in self.participants:
            hook = getattr(participant, "state_fragments", None)
            if hook is None:
                continue
            try:
                fragments.extend(hook())
            except Exception as exc:  # noqa: BLE001
                self._report(
                    phase="lifecycle.state_fragments",
                    participant=participant,
                    exc=exc,
                )
        return fragments

    def _report(self, *, phase: str, participant, exc: Exception, context: dict | None = None) -> None:  # noqa: ANN001
        if self.fault_reporter is None:
            return
        self.fault_reporter(
            phase=phase,
            source_type="lifecycle_participant",
            source_name=self._participant_name(participant),
            exc=exc,
            context=context,
            emit_event=True,
        )

    @staticmethod
    def _participant_name(participant) -> str:  # noqa: ANN001
        return str(
            getattr(participant, "participant_name", None)
            or getattr(participant, "capability_name", None)
            or participant.__class__.__name__
        )
