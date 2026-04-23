from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from governance.protocol_index import ProtocolIndexer


def test_entity_pages_follow_type_pattern() -> None:
    result = ProtocolIndexer(ROOT).scan()
    assert result.entities
    for entity_id, node in result.entities.items():
        parts = entity_id.split("/")
        assert Path(node.path).name == f"{parts[0]}.md"
