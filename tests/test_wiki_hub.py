from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from runtime.engine import Engine
from agents.wiki_front_chat import build_engine as build_wiki_front_engine


def build_engine() -> Engine:
    return build_wiki_front_engine(
        {
            "provider": "mock",
            "model": "mock",
            "api_key": None,
            "base_url": None,
            "user_id": "test_user",
            "conversation_id": "wiki_suite",
            "task_id": "case_001",
        }
    )


def test_wiki_toolbox_attached() -> None:
    engine = build_engine()
    assert "wiki" in [toolbox.toolbox_name for toolbox in engine.toolboxes]


def test_wiki_refresh_and_search() -> None:
    engine = build_engine()
    payload = json.loads(engine.refresh_wiki())
    assert payload["status"] == "ok"
    results = json.loads(engine.knowledge_hub.search("inventory"))
    assert isinstance(results, list)


def test_attachment_ingest_contract() -> None:
    engine = build_engine()
    result = engine.ingest_files([{"name": "missing.txt", "url": "file:///tmp/does_not_exist.txt"}])
    assert isinstance(result, str)
