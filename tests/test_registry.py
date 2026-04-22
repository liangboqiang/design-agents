from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from governance.registry import GovernanceRegistry


def test_registry_scans_skills_tools_and_agents() -> None:
    registry = GovernanceRegistry(ROOT)
    assert "general/root" in registry.skills
    assert "parts_design/root" in registry.skills
    assert "general_chat" in registry.agent_specs
    assert "parts_design_chat" in registry.agent_specs
    assert "files" in registry.toolboxes
    assert "shell" in registry.toolboxes
    assert "system_prompt.md" in registry.context_assets

