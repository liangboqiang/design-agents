from __future__ import annotations

from pathlib import Path

from control.protocol_index import ProtocolIndexer, ProtocolIndexResult


class AssetCatalog:
    """Thin catalog facade over the protocol index read model."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.indexer = ProtocolIndexer(self.project_root)

    def scan(self) -> ProtocolIndexResult:
        return self.indexer.scan()

    def refresh_store(self) -> ProtocolIndexResult:
        return self.indexer.refresh_store()

    def load_store(self) -> tuple[dict, dict, dict]:
        return self.indexer.load_store()
