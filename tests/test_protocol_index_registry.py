from __future__ import annotations

from pathlib import Path

from governance.protocol_index import ProtocolIndexer
from governance.registry import GovernanceRegistry


ROOT = Path(__file__).resolve().parents[1]


def test_protocol_index_emits_structured_nodes() -> None:
    result = ProtocolIndexer(ROOT).scan()

    tool_node = result.entities["tool/wiki_admin/refresh_system"]
    assert tool_node.title == "Refresh Wiki System"
    assert tool_node.summary == "Refresh the shared wiki index and system summaries."
    assert tool_node.runtime_action == "wiki_admin.refresh_system"

    agent_node = result.entities["agent/wiki_front_chat"]
    assert agent_node.section_links["root skill"] == ["skill/wiki_hub/root"]
    assert agent_node.code_items["toolboxes"] == ["wiki", "wiki_admin"]
    assert agent_node.settings["max_prompt_chars"] == "22000"
    assert agent_node.settings["provider"] == "mock"


def test_registry_consumes_protocol_index_for_skills_and_agents() -> None:
    registry = GovernanceRegistry(ROOT)

    ingest_skill = registry.get_skill("skill/wiki_hub/ingest")
    assert ingest_skill.actions == ["wiki_admin.refresh_system", "wiki_admin.ingest_files"]
    assert ingest_skill.refs == ["skill/governance/agent_build"]

    agent_spec = registry.get_agent_spec("wiki_front_chat")
    assert agent_spec.root_skill == "skill/wiki_hub/root"
    assert agent_spec.toolboxes == ["wiki", "wiki_admin"]
    assert agent_spec.capabilities == ["subagent", "compact"]
    assert agent_spec.context_policy["max_prompt_chars"] == 22000
    assert agent_spec.llm == {"provider": "mock", "model": "mock"}
