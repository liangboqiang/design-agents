from __future__ import annotations


class CompactPolicy:
    def __init__(self, *, threshold: int):
        self.threshold = threshold

    def should_compact(self, estimated_size: int) -> bool:
        return estimated_size > self.threshold

