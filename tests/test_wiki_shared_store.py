from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from runtime.engine import Engine
from shared.paths import project_root
from wiki.store import WikiStore
from agents.wiki_front_chat import build_engine as build_wiki_front_engine


def build_engine() -> Engine:
    return build_wiki_front_engine(
        {
            "provider": "mock",
            "model": "mock",
            "user_id": "test_user",
            "conversation_id": "wiki_suite",
            "task_id": "case_001",
        }
    )


def test_wiki_toolboxes_partitioned() -> None:
    engine = build_engine()
    names = [toolbox.toolbox_name for toolbox in engine.toolboxes]
    assert "wiki" in names
    assert "wiki_admin" in names
    assert "shell" not in names
    assert "files" not in names


def test_wiki_store_path_shared() -> None:
    store = WikiStore(project_root())
    store.ensure()
    assert store.root == project_root() / "data" / "wiki"


def test_refresh_returns_status_json() -> None:
    engine = build_engine()
    result = json.loads(engine.refresh_wiki())
    assert result["status"] == "ok"
