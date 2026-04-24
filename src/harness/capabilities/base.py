from __future__ import annotations

from abc import ABC
from typing import Iterable

from schemas.action import ActionSpec


class Capability(ABC):
    capability_name: str

    def bind(self, runtime, capability_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime
        self._capability_lookup = capability_lookup or (lambda name: None)

    def capability(self, name: str):
        return self._capability_lookup(name)

    def action_specs(self) -> Iterable[ActionSpec]:
        return []

    def before_user_turn(self, message: str) -> None:
        return None

    def before_model_call(self) -> None:
        return None

    def after_tool_call(self, action_id: str, result: str) -> None:
        return None

    def state_fragments(self) -> list[str]:
        return []

