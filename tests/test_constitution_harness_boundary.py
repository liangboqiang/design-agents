from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from runtime.harness import Harness


def test_harness_has_no_direct_wiki_dependency() -> None:
    source = inspect.getsource(Harness)
    assert "wiki_hub" not in source
    assert "ingest_user_files" not in source
