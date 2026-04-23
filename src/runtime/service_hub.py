from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ServiceHub:
    knowledge_hub: Any
    attachment_ingestion: Any | None = None
