from __future__ import annotations

from schemas.action import ActionSpec

from .faults import ActionExecutionResult


class Dispatcher:
    def __init__(self, registry: dict[str, ActionSpec], fault_reporter=None):  # noqa: ANN001
        self.registry = registry
        self.fault_reporter = fault_reporter

    def dispatch(self, action_id: str, arguments: dict) -> ActionExecutionResult:
        if action_id not in self.registry:
            fault = None
            if self.fault_reporter is not None:
                fault = self.fault_reporter(
                    phase="tool_dispatch",
                    source_type="action",
                    source_name=action_id,
                    message=f"Unknown action '{action_id}'.",
                    context={"arguments": arguments},
                    emit_event=True,
                    exc_type="UnknownActionError",
                )
            content = (
                fault.user_message()
                if fault is not None
                else f"Error: unknown action '{action_id}'."
            )
            return ActionExecutionResult(
                ok=False,
                action_id=action_id,
                content=content,
                meta={"error_code": "unknown_action"},
                fault=fault,
            )
        try:
            result = self.registry[action_id].executor(arguments)
            if isinstance(result, ActionExecutionResult):
                return result
            return ActionExecutionResult.from_value(action_id, result)
        except Exception as exc:  # noqa: BLE001
            fault = None
            if self.fault_reporter is not None:
                fault = self.fault_reporter(
                    phase="tool_dispatch",
                    source_type="action",
                    source_name=action_id,
                    exc=exc,
                    context={"arguments": arguments},
                    emit_event=True,
                )
            content = (
                fault.user_message()
                if fault is not None
                else f"Error while executing {action_id}: {exc}"
            )
            return ActionExecutionResult.from_fault(
                action_id,
                fault
                if fault is not None
                else self._fallback_fault(action_id, str(exc), arguments),
                content=content,
                meta={"error_code": "action_exception"},
            )

    @staticmethod
    def _fallback_fault(action_id: str, message: str, arguments: dict):
        from .faults import RuntimeFault

        return RuntimeFault.from_message(
            phase="tool_dispatch",
            source_type="action",
            source_name=action_id,
            message=message,
            context={"arguments": arguments},
        )
