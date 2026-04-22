from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from time import time
from typing import Any, Generic, TypeVar
from uuid import uuid4


T = TypeVar("T")


def _safe_text(value: Any, *, limit: int = 400) -> str:
    text = str(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


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
        return (
            f"Runtime failure [{self.phase}] in {self.source_name} "
            f"(trace_id={self.trace_id}): {self.message}"
        )


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
        return cls(
            ok=True,
            action_id=action_id,
            content="" if value is None else str(value),
            raw_result=value,
        )

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
