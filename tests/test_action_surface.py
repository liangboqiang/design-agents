from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agents.parts_design_chat import build_engine


def test_action_surface_is_deduped_and_includes_workspace_actions() -> None:
    engine = build_engine({"provider": "mock", "model": "mock", "api_key": None, "base_url": None})
    surface = engine.action_compiler.compile_surface(
        skill_runtime=engine.skill_runtime,
        action_registry=engine.action_registry,
        state_fragments=engine.lifecycle.state_fragments(),
        recent_events=engine.events.recent(),
    )
    action_ids = [spec.action_id for spec in surface.visible_actions]
    assert len(action_ids) == len(set(action_ids))
    assert "workspace.create" in action_ids
    assert "workspace.run" in action_ids

