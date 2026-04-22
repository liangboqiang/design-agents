from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from design_agents.engine import Engine
from design_agents.llm.coding_plan import (
    CODING_PLAN_ANTHROPIC_BASE_URL,
    CODING_PLAN_OPENAI_BASE_URL,
    DEFAULT_CODING_PLAN_MODEL,
    resolve_anthropic_base_url,
    resolve_coding_plan_api_key,
    resolve_openai_base_url,
)
from design_agents.toolboxes.files import FileToolbox


def main() -> None:
    assert DEFAULT_CODING_PLAN_MODEL == "qwen3-coder-plus"
    assert resolve_openai_base_url(None) == CODING_PLAN_OPENAI_BASE_URL
    assert resolve_anthropic_base_url(None) == CODING_PLAN_ANTHROPIC_BASE_URL
    assert resolve_coding_plan_api_key("sk-sp-self-check") == "sk-sp-self-check"

    engine = Engine(
        skill_root=Path("skills/domains/general/root"),
        provider="mock",
        model="mock",
        toolboxes=[FileToolbox()],
        enhancements=["todo", "task", "compact"],
        user_id="check_user",
        conversation_id="check_conversation",
        task_id="check_task",
    )
    print(engine.chat('/call engine.inspect_skill {"skill":"domains/general/root"}'))
    print(engine.chat('/call todo.update {"items":[{"id":"1","text":"read skill","status":"in_progress"}]}'))
    print(engine.chat('/call task.create {"subject":"demo task","description":"demo"}'))
    print(engine.chat('/call task.list {}'))
    print("self check finished")


if __name__ == "__main__":
    main()
