from __future__ import annotations

import json
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Any, Callable, Generic, TypeVar
from uuid import uuid4


T = TypeVar("T")


def _safe_text(value: Any, *, limit: int = 400) -> str:
    text = str(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return repr(value)


@dataclass(slots=True)
class RuntimeFault:
    trace_id: str
    phase: str
    source_type: str
    source_name: str
    exc_type: str
    message: str
    detail: str = ""
    stacktrace: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time)

    @classmethod
    def from_exception(
        cls,
        *,
        phase: str,
        source_type: str,
        source_name: str,
        exc: Exception,
        context: dict[str, Any] | None = None,
    ) -> "RuntimeFault":
        return cls(
            trace_id=f"rtf_{uuid4().hex[:12]}",
            phase=phase,
            source_type=source_type,
            source_name=source_name,
            exc_type=exc.__class__.__name__,
            message=_safe_text(exc),
            detail=repr(exc),
            stacktrace=traceback.format_exc(),
            context=dict(context or {}),
        )

    @classmethod
    def from_message(
        cls,
        *,
        phase: str,
        source_type: str,
        source_name: str,
        message: str,
        context: dict[str, Any] | None = None,
        exc_type: str = "RuntimeError",
    ) -> "RuntimeFault":
        return cls(
            trace_id=f"rtf_{uuid4().hex[:12]}",
            phase=phase,
            source_type=source_type,
            source_name=source_name,
            exc_type=exc_type,
            message=_safe_text(message),
            detail=str(message),
            stacktrace="",
            context=dict(context or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "phase": self.phase,
            "source_type": self.source_type,
            "source_name": self.source_name,
            "exc_type": self.exc_type,
            "message": self.message,
            "detail": self.detail,
            "stacktrace": self.stacktrace,
            "context": self.context,
            "ts": self.ts,
        }

    def user_message(self) -> str:
        return f"Runtime failure [{self.phase}] in {self.source_name} (trace_id={self.trace_id}): {self.message}"


@dataclass(slots=True)
class GuardResult(Generic[T]):
    ok: bool
    value: T | None = None
    fault: RuntimeFault | None = None


@dataclass(slots=True)
class ActionExecutionResult:
    ok: bool
    action_id: str
    content: str
    raw_result: Any = None
    fault: RuntimeFault | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def trace_id(self) -> str:
        return self.fault.trace_id if self.fault is not None else ""

    @classmethod
    def from_value(cls, action_id: str, value: Any) -> "ActionExecutionResult":
        return cls(ok=True, action_id=action_id, content="" if value is None else str(value), raw_result=value)

    @classmethod
    def from_fault(
        cls,
        action_id: str,
        fault: RuntimeFault,
        *,
        content: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> "ActionExecutionResult":
        return cls(
            ok=False,
            action_id=action_id,
            content=content or fault.user_message(),
            raw_result=None,
            fault=fault,
            meta=dict(meta or {}),
        )

    def __str__(self) -> str:
        return self.content


class FailureSink:
    def __init__(self, *, session, audit, events, runtime_state=None):  # noqa: ANN001
        self.session = session
        self.audit = audit
        self.events = events
        self.runtime_state = runtime_state
        self.log_path = Path(self.session.paths.logs_dir) / "runtime_faults.jsonl"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def record_fault(self, fault: RuntimeFault, *, emit_event: bool = True) -> RuntimeFault:
        if self.runtime_state is not None:
            self.runtime_state.last_fault = fault
            history = list(getattr(self.runtime_state, "fault_history", []))
            history.append(fault.trace_id)
            self.runtime_state.fault_history = history[-20:]

        self.audit.record(
            "runtime.fault",
            trace_id=fault.trace_id,
            phase=fault.phase,
            source_type=fault.source_type,
            source_name=fault.source_name,
            exc_type=fault.exc_type,
            message=fault.message,
            context=_json_safe(fault.context),
        )

        with self.log_path.open("a", encoding="utf-8") as fh:
            payload = fault.to_dict()
            payload["context"] = _json_safe(payload.get("context"))
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")

        if emit_event and self.events is not None:
            try:
                self.events.emit(
                    "runtime.fault",
                    trace_id=fault.trace_id,
                    phase=fault.phase,
                    source_type=fault.source_type,
                    source_name=fault.source_name,
                    exc_type=fault.exc_type,
                    message=fault.message,
                    user_message=fault.user_message(),
                )
            except Exception:
                pass

        return fault

    def recent_faults(self, limit: int = 10) -> list[dict[str, Any]]:
        if not self.log_path.exists():
            return []
        rows = self.log_path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in rows[-limit:] if line.strip()]


class TurnGuard:
    def __init__(self, sink: FailureSink):
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
