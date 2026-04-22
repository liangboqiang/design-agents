from __future__ import annotations

import json
import time

from agents.capabilities.base import Capability
from agents.core.models import ActionSpec
from agents.core.storage import JsonlStore


class CompactCapability(Capability):
    capability_name = "compact"

    def bind(self, engine) -> None:
        super().bind(engine)
        self.transcripts = JsonlStore(engine.paths.logs_dir / "transcripts.jsonl")

    def action_specs(self):
        return [ActionSpec("compact.now", "Compact context", "手动压缩当前上下文，把旧历史摘要化。", {"type": "object", "properties": {}}, lambda args: self.compact_now(), "capability.compact")]

    def before_model_call(self) -> None:
        self._micro_compact()
        if self._estimate_size() > self.engine.settings.auto_compact_threshold:
            self.compact_now()

    def _micro_compact(self) -> None:
        rows = self.engine.history.read()
        if len(rows) <= self.engine.settings.history_keep_turns:
            return
        compacted = rows[-self.engine.settings.history_keep_turns:]
        if len(rows) > len(compacted):
            self.transcripts.append({"ts": time.time(), "type": "micro_compact", "dropped": len(rows) - len(compacted)})
            self.engine.history.replace(compacted)

    def _estimate_size(self) -> int:
        return sum(len(json.dumps(item, ensure_ascii=False)) for item in self.engine.history.read())

    def compact_now(self) -> str:
        rows = self.engine.history.read()
        if not rows:
            return "No history to compact."
        summary = "\n".join(f"[{item['role']}] {str(item['content'])[:300]}" for item in rows[-12:])
        self.transcripts.append({"ts": time.time(), "type": "full_compact", "rows": rows})
        self.engine.history.replace([{"role": "system", "content": f"[COMPACTED SUMMARY]\n{summary}"}])
        return "Context compacted."
