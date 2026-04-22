from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from runtime.engine import Engine


def test_engine_does_not_inject_hidden_wiki_toolbox() -> None:
    engine = Engine(
        skill_root="general/root",
        provider="mock",
        model="mock",
        api_key=None,
        base_url=None,
        user_id="constitution",
        conversation_id="case",
        task_id="001",
        toolboxes=["files"],
        enhancements=[],
    )
    toolbox_names = [toolbox.toolbox_name for toolbox in engine.toolboxes]
    assert toolbox_names == ["files"]
    assert "wiki" not in toolbox_names
