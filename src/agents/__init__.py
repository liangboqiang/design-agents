"""Agent entrypoints and spec loaders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.engine import Engine, load_agent_spec


def build_from_spec(spec_filename: str, overrides: dict[str, Any] | None = None) -> Engine:
    spec_path = Path(__file__).with_name("specs") / spec_filename
    spec = load_agent_spec(spec_path)
    return Engine.from_agent_spec(spec, **(overrides or {}))

