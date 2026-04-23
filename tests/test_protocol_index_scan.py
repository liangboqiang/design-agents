from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from governance.protocol_index import ProtocolIndexer


def test_protocol_index_writes_store_files() -> None:
    indexer = ProtocolIndexer(ROOT)
    result = indexer.refresh_store()
    assert result.entities
    assert indexer.index_path.exists()
    assert indexer.catalog_path.exists()
    assert indexer.graph_path.exists()
