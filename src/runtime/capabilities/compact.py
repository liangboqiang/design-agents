from __future__ import annotations

import json
import time

from context.compaction.micro_compact import micro_compact
from context.compaction.summary_compact import build_summary
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
        if self._estimate_size() > self.engine.settings.auto_compact_threshold:
            self.compact_now()

    def _micro_compact(self) -> None:
        rows = self.engine.read_history()
        compacted = micro_compact(rows, keep_turns=self.engine.settings.history_keep_turns)
        if len(compacted) < len(rows):
            self.engine.session.transcripts.append(
                {"ts": time.time(), "type": "micro_compact", "dropped": len(rows) - len(compacted)}
            )
            self.engine.replace_history(compacted)

    def _estimate_size(self) -> int:
        return sum(len(json.dumps(row, ensure_ascii=False)) for row in self.engine.read_history())

    def compact_now(self) -> str:
        rows = self.engine.read_history()
        if not rows:
            return "No history to compact."
        summary = build_summary(rows)
        self.engine.session.transcripts.append({"ts": time.time(), "type": "full_compact", "rows": rows})
        self.engine.replace_history([{"role": "system", "content": f"[COMPACTED SUMMARY]\n{summary}"}])
        self.engine.events.emit("compact.performed", summary=summary)
        return "Context compacted."

