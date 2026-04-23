from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from runtime.engine import Engine
from agent.wiki_front_chat import build_engine as build_wiki_front_engine


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


def test_wiki_admin_toolbox_attached() -> None:
    engine = build_engine()
    assert "wiki_admin" in [toolbox.toolbox_name for toolbox in engine.toolboxes]


def test_wiki_refresh_builds_shared_store() -> None:
    engine = build_engine()
    payload = json.loads(engine.refresh_wiki())
    assert payload["status"] == "ok"
    assert payload["root"].endswith("src\\wiki_store") or payload["root"].endswith("src/wiki_store")
    assert Path(payload["catalog_path"]).exists()


def test_wiki_refresh_and_search() -> None:
    engine = build_engine()
    engine.refresh_wiki()
    results = json.loads(engine.knowledge_hub.search("wiki", limit=5))
    assert isinstance(results, list)


def test_attachment_ingest_contract() -> None:
    engine = build_engine()
    result = json.loads(engine.ingest_files([{"name": "missing.txt", "url": "file:///tmp/does_not_exist.txt"}]))
    assert result["status"] == "ok"
