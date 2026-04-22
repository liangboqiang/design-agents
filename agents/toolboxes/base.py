from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable

from agents.core.models import ActionSpec


class Toolbox(ABC):
    toolbox_name: str
    workspace_root: Path | None

    @abstractmethod
    def action_specs(self) -> Iterable[ActionSpec]:
        raise NotImplementedError

    @abstractmethod
    def spawn(self, workspace_root: Path) -> "Toolbox":
        raise NotImplementedError
