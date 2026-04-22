from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agents.general_chat import build_engine


def test_context_assembler_builds_layered_prompt() -> None:
    engine = build_engine({"provider": "mock", "model": "mock", "api_key": None, "base_url": None})
    state_fragments = engine.lifecycle.state_fragments()
    surface = engine.action_compiler.compile_surface(
        skill_runtime=engine.skill_runtime,
        action_registry=engine.action_registry,
        state_fragments=state_fragments,
        recent_events=engine.events.recent(),
    )
    prompt = engine.context_assembler.build_system_prompt(
        engine_context=engine.context,
        skill_runtime=engine.skill_runtime,
        surface_snapshot=surface,
        history_rows=engine.read_history(),
        state_fragments=state_fragments,
        recent_events=engine.events.recent(),
        audit=engine.audit,
        registry=engine.registry,
    )
    assert "## Identity" in prompt
    assert "## Visible Actions" in prompt
    assert "## Response Contract" in prompt

