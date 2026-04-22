from __future__ import annotations

from design_agents.capabilities.autonomy import AutonomyCapability
from design_agents.capabilities.background import BackgroundCapability
from design_agents.capabilities.compact import CompactCapability
from design_agents.capabilities.isolation import IsolationCapability
from design_agents.capabilities.protocol import ProtocolCapability
from design_agents.capabilities.subagent import SubagentCapability
from design_agents.capabilities.task import TaskCapability
from design_agents.capabilities.team import TeamCapability
from design_agents.capabilities.todo import TodoCapability
from design_agents.capabilities.workspace import WorkspaceCapability


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
