from __future__ import annotations

import json
import time

from context.history import build_summary, micro_compact
from schemas.action import ActionSpec

from .base import Capability


class CompactCapability(Capability):
    capability_name = "compact"

    def action_specs(self):
        return [
            ActionSpec(
                "compact.now",
                "Compact context",
                "Compact the current conversation history into a shorter summary.",
                {"type": "object", "properties": {}},
                lambda args: self.compact_now(),
                "capability.compact",
            )
        ]

    def before_model_call(self) -> None:
        self._micro_compact()
        if self._estimate_size() > self.runtime.settings.auto_compact_threshold:
            self.compact_now()

    def _micro_compact(self) -> None:
        rows = self.runtime.session.history.read()
        compacted = micro_compact(rows, keep_turns=self.runtime.settings.history_keep_turns)
        if len(compacted) < len(rows):
            self.runtime.session.transcripts.append(
                {"ts": time.time(), "type": "micro_compact", "dropped": len(rows) - len(compacted)}
            )
            self.runtime.session.history.replace(compacted)

    def _estimate_size(self) -> int:
        return sum(len(json.dumps(row, ensure_ascii=False)) for row in self.runtime.session.history.read())

    def compact_now(self) -> str:
        rows = self.runtime.session.history.read()
        if not rows:
            return "No history to compact."
        summary = build_summary(rows)
        self.runtime.session.transcripts.append({"ts": time.time(), "type": "full_compact", "rows": rows})
        self.runtime.session.history.replace([{"role": "system", "content": f"[COMPACTED SUMMARY]\n{summary}"}])
        self.runtime.events.emit("compact.performed", summary=summary)
        return "Context compacted."
