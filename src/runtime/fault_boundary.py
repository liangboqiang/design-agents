from __future__ import annotations

from typing import Any, Callable, TypeVar

from .faults import GuardResult, RuntimeFault


T = TypeVar("T")


class FaultBoundary:
    def __init__(self, sink):  # noqa: ANN001
        self.sink = sink

    def call(
        self,
        *,
        phase: str,
        source_type: str,
        source_name: str,
        fn: Callable[[], T],
        context: dict[str, Any] | None = None,
        emit_event: bool = True,
    ) -> GuardResult[T]:
        try:
            return GuardResult(ok=True, value=fn())
        except Exception as exc:  # noqa: BLE001
            fault = RuntimeFault.from_exception(
                phase=phase,
                source_type=source_type,
                source_name=source_name,
                exc=exc,
                context=context,
            )
            self.sink.record_fault(fault, emit_event=emit_event)
            return GuardResult(ok=False, fault=fault)

    def report(
        self,
        *,
        phase: str,
        source_type: str,
        source_name: str,
        exc: Exception | None = None,
        message: str | None = None,
        context: dict[str, Any] | None = None,
        emit_event: bool = True,
        exc_type: str = "RuntimeError",
    ) -> RuntimeFault:
        if exc is not None:
            fault = RuntimeFault.from_exception(
                phase=phase,
                source_type=source_type,
                source_name=source_name,
                exc=exc,
                context=context,
            )
        else:
            fault = RuntimeFault.from_message(
                phase=phase,
                source_type=source_type,
                source_name=source_name,
                message=message or "Unknown runtime failure",
                context=context,
                exc_type=exc_type,
            )
        return self.sink.record_fault(fault, emit_event=emit_event)
