from __future__ import annotations

from abc import ABC
from typing import Iterable

from schemas.action import ActionSpec


class Capability(ABC):
    capability_name: str

    def bind(self, runtime) -> None:  # noqa: ANN001
        self.runtime = runtime

    def capability(self, name: str):
        return next(
            (capability for capability in self.runtime.capabilities if capability.capability_name == name),
            None,
        )

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

