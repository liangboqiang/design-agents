from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .faults import RuntimeFault


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return repr(value)


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
                # Event emission should never block fault persistence.
                pass

        return fault

    def recent_faults(self, limit: int = 10) -> list[dict[str, Any]]:
        if not self.log_path.exists():
            return []
        rows = self.log_path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in rows[-limit:] if line.strip()]
