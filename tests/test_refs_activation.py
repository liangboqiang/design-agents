from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agents.general_chat import build_engine


def test_refs_and_events_activate_governance_skills() -> None:
    engine = build_engine({"provider": "mock", "model": "mock", "api_key": None, "base_url": None})
    engine.events.emit("task.blocked", task_id=1, blocked_by=[2])
    engine.events.emit("workspace.created", workspace={"name": "w1"})
    surface = engine.action_compiler.compile_surface(
        skill_runtime=engine.skill_runtime,
        action_registry=engine.action_registry,
        state_fragments=engine.lifecycle.state_fragments(),
        recent_events=engine.events.recent(),
    )
    assert "governance/refs_bridge" in surface.activated_skill_ids
    assert "governance/task_governance" in surface.activated_skill_ids
    assert "governance/workspace_governance" in surface.activated_skill_ids
