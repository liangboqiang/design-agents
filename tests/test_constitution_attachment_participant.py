from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agents.general_chat import build_engine


def test_attachment_ingestion_is_owned_by_lifecycle_participant() -> None:
    engine = build_engine(
        {
            "provider": "mock",
            "model": "mock",
            "api_key": None,
            "base_url": None,
            "user_id": "constitution",
            "conversation_id": "attachment-case",
            "task_id": "001",
        }
    )
    engine.lifecycle.before_user_turn(
        "Please read the attachment.",
        files=[{"name": "missing.txt", "url": "file:///tmp/does_not_exist.txt"}],
    )
    snapshot = engine.read_state_json("attachment_ingest.json", {})
    assert snapshot["file_count"] == 1
    assert snapshot["file_names"] == ["missing.txt"]
