from __future__ import annotations

from .base import Capability


class IsolationCapability(Capability):
    capability_name = "isolation"

    def __init__(self, mode: str = "data"):
        self.mode = mode

    def state_fragments(self) -> list[str]:
        return [f"isolation_mode: {self.mode}"]
