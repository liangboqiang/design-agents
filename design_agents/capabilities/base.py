from __future__ import annotations

from abc import ABC
from typing import Iterable

from design_agents.core.models import ActionSpec


class Capability(ABC):
    capability_name: str

    def bind(self, engine) -> None:  # noqa: ANN001
        self.engine = engine

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
