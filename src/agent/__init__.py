"""Agent entrypoints backed by markdown truth pages."""

from __future__ import annotations

from typing import Any

from governance.registry import GovernanceRegistry
from runtime.engine import Engine
from shared.paths import project_root


def build_from_page(agent_name: str, overrides: dict[str, Any] | None = None) -> Engine:
    merged = dict(overrides or {})
    registry = merged.pop("registry", None) or GovernanceRegistry(project_root())
    spec = registry.get_agent_spec(agent_name)
    return Engine.from_agent_spec(spec, registry=registry, **merged)
