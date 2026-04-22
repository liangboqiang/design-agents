from __future__ import annotations

import json
import subprocess
import threading
import uuid
from pathlib import Path
from typing import Iterable

from schemas.action import ActionSpec
from tools.indexes.toolbox_registry import Toolbox


class MCPStdIOToolbox(Toolbox):
    """Minimal stdio MCP client for initialize/tools/list/tools/call servers."""

    toolbox_name = "mcp_stdio"
    discoverable = False
    tags = ("mcp",)

    def __init__(
        self,
        command: list[str] | None = None,
        toolbox_name: str | None = None,
        cwd: Path | None = None,
        workspace_root: Path | None = None,
    ):
        super().__init__(workspace_root=workspace_root)
        self.command = command or ["python", "-c", "print()"]
        self.toolbox_name = toolbox_name or self.toolbox_name
        self.cwd = cwd
        self._proc: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()
        self._actions: dict[str, dict] | None = None

    def spawn(self, workspace_root: Path) -> "MCPStdIOToolbox":
        return MCPStdIOToolbox(
            command=list(self.command),
            toolbox_name=self.toolbox_name,
            cwd=self.cwd,
            workspace_root=workspace_root,
        )

    def _ensure_proc(self) -> None:
        if self._proc is not None:
            return
        self._proc = subprocess.Popen(
            self.command,
            cwd=self.cwd or self.workspace_root,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "design-agents", "version": "0.2.0"},
                "capabilities": {},
            },
        )
        self._notify("notifications/initialized", {})

    def _request(self, method: str, params: dict) -> dict:
        self._ensure_proc()
        assert self._proc and self._proc.stdin and self._proc.stdout
        with self._lock:
            req_id = str(uuid.uuid4())
            self._proc.stdin.write(
                json.dumps({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}) + "\n"
            )
            self._proc.stdin.flush()
            while True:
                line = self._proc.stdout.readline()
                if not line:
                    raise RuntimeError(f"MCP server terminated while waiting for {method}")
                message = json.loads(line)
                if message.get("id") == req_id:
                    if "error" in message:
                        raise RuntimeError(message["error"])
                    return message.get("result") or {}

    def _notify(self, method: str, params: dict) -> None:
        self._ensure_proc()
        assert self._proc and self._proc.stdin
        with self._lock:
            self._proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method, "params": params}) + "\n")
            self._proc.stdin.flush()

    def _list_tools(self) -> dict[str, dict]:
        if self._actions is not None:
            return self._actions
        result = self._request("tools/list", {})
        self._actions = {tool["name"]: tool for tool in (result.get("tools") or [])}
        return self._actions

    def action_specs(self) -> Iterable[ActionSpec]:
        specs: list[ActionSpec] = []
        for tool_name, tool in self._list_tools().items():
            specs.append(
                ActionSpec(
                    f"{self.toolbox_name}.{tool_name}",
                    tool.get("title") or tool_name,
                    tool.get("description") or f"MCP tool {tool_name}",
                    tool.get("inputSchema") or {"type": "object", "properties": {}},
                    lambda args, _name=tool_name: self._call(_name, args),
                    self.toolbox_name,
                    json.dumps(tool, ensure_ascii=False, indent=2),
                    tags=("mcp",),
                )
            )
        return specs

    def _call(self, tool_name: str, args: dict) -> str:
        result = self._request("tools/call", {"name": tool_name, "arguments": args})
        return json.dumps(result, ensure_ascii=False, indent=2)

