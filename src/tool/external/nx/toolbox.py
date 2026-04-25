from __future__ import annotations

from pathlib import Path

from tool.mcp_stdio import MCPStdIOToolbox


class NXToolbox(MCPStdIOToolbox):
    toolbox_name = "nx"
    discoverable = False

    def __init__(self, command: list[str] | None = None, workspace_root: Path | None = None):
        super().__init__(command=command or ["python", "-c", "print()"], toolbox_name=self.toolbox_name, workspace_root=workspace_root)
