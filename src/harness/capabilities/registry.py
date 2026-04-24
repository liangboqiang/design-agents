from __future__ import annotations

from .autonomy import AutonomyCapability
from .background import BackgroundCapability
from .compact import CompactCapability
from .isolation import IsolationCapability
from .protocol import ProtocolCapability
from .subagent import SubagentCapability
from .task import TaskCapability
from .team import TeamCapability
from .todo import TodoCapability
from .workspace import WorkspaceCapability


def create_capability(name: str):
    normalized = name.strip().lower()
    if normalized == "todo":
        return TodoCapability()
    if normalized == "subagent":
        return SubagentCapability()
    if normalized == "compact":
        return CompactCapability()
    if normalized == "task":
        return TaskCapability()
    if normalized == "background":
        return BackgroundCapability()
    if normalized == "team":
        return TeamCapability()
    if normalized == "protocol":
        return ProtocolCapability()
    if normalized == "autonomy":
        return AutonomyCapability()
    if normalized == "workspace":
        return WorkspaceCapability()
    if normalized.startswith("isolation"):
        _, _, mode = normalized.partition(":")
        return IsolationCapability(mode or "data")
    raise ValueError(f"Unknown capability: {name}")

