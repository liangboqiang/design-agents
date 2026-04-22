from __future__ import annotations

import json
import time

from agents.capabilities.base import Capability
from agents.core.models import ActionSpec


class CompactCapability(Capability):
    capability_name = "compact"
    transcripts_file = "compact_transcripts.json"

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

    def _append_transcript(self, entry: dict) -> None:
        rows = self.engine.read_state_json(self.transcripts_file, [])
        rows.append(entry)
        self.engine.write_state_json(self.transcripts_file, rows)

    def _micro_compact(self) -> None:
        rows = self.engine.read_history()
        if len(rows) <= self.engine.settings.history_keep_turns:
            return
        compacted = rows[-self.engine.settings.history_keep_turns :]
        if len(rows) > len(compacted):
            self._append_transcript(
                {
                    "ts": time.time(),
                    "type": "micro_compact",
                    "dropped": len(rows) - len(compacted),
                }
            )
            self.engine.replace_history(compacted)

    def _estimate_size(self) -> int:
        return sum(len(json.dumps(item, ensure_ascii=False)) for item in self.engine.read_history())

    def compact_now(self) -> str:
        rows = self.engine.read_history()
        if not rows:
            return "No history to compact."

        summary = "\n".join(f"[{item['role']}] {str(item['content'])[:300]}" for item in rows[-12:])
        self._append_transcript(
            {
                "ts": time.time(),
                "type": "full_compact",
                "rows": rows,
            }
        )
        self.engine.replace_history(
            [{"role": "system", "content": f"[COMPACTED SUMMARY]\n{summary}"}]
        )
        return "Context compacted."
