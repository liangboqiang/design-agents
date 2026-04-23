from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from governance.protocol_index import ProtocolIndexer


def test_protocol_links_resolve() -> None:
    result = ProtocolIndexer(ROOT).scan()
    resolvable = set(result.entities) | set(result.pages)
    for edge in result.edges:
        assert edge["from"] in resolvable
        assert edge["to"] in resolvable
