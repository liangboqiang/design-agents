from __future__ import annotations

from pathlib import Path


class ContextIndex:
    def __init__(self, context_root: Path):
        self.context_root = context_root
        self.assets = self._scan()

    def _scan(self) -> dict[str, Path]:
        if not self.context_root.exists():
            return {}
        mappings = {
            "system_prompt.md": self.context_root / "system" / "default" / "template.txt",
            "tool_result.md": self.context_root / "tool_result" / "default" / "template.txt",
            "compact_summary.md": self.context_root / "compact_summary" / "default" / "template.txt",
        }
        return {name: path for name, path in mappings.items() if path.exists()}

    def get(self, name: str) -> Path:
        return self.assets[name]

