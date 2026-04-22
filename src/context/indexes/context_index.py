from __future__ import annotations

from pathlib import Path


class ContextIndex:
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.assets = self._scan()

    def _scan(self) -> dict[str, Path]:
        if not self.templates_dir.exists():
            return {}
        return {path.name: path for path in sorted(self.templates_dir.glob("*")) if path.is_file()}

    def get(self, name: str) -> Path:
        return self.assets[name]

