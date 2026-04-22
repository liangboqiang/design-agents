from __future__ import annotations

from agents.capabilities.autonomy import AutonomyCapability
from agents.capabilities.background import BackgroundCapability
from agents.capabilities.compact import CompactCapability
from agents.capabilities.isolation import IsolationCapability
from agents.capabilities.protocol import ProtocolCapability
from agents.capabilities.subagent import SubagentCapability
from agents.capabilities.task import TaskCapability
from agents.capabilities.team import TeamCapability
from agents.capabilities.todo import TodoCapability
from agents.capabilities.workspace import WorkspaceCapability


def create_capability(name: str):
    normalized = name.strip().lower()
    if normalized == "todo": return TodoCapability()
    if normalized == "subagent": return SubagentCapability()
    if normalized == "compact": return CompactCapability()
    if normalized == "task": return TaskCapability()
    if normalized == "background": return BackgroundCapability()
    if normalized == "team": return TeamCapability()
    if normalized == "protocol": return ProtocolCapability()
    if normalized == "autonomy": return AutonomyCapability()
    if normalized == "workspace": return WorkspaceCapability()
    if normalized.startswith("isolation"):
        _, _, mode = normalized.partition(":")
        return IsolationCapability(mode or "data")
    raise ValueError(f"Unknown capability: {name}")
