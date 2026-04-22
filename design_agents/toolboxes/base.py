from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from design_agents.core.models import ActionSpec


class Toolbox(ABC):
    toolbox_name: str

    @abstractmethod
    def action_specs(self) -> Iterable[ActionSpec]:
        raise NotImplementedError
