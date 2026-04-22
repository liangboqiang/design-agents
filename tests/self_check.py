from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.engine import Engine
from agents.llm.config import DEFAULT_MODEL, DEFAULT_PROVIDER, resolve_model, resolve_provider
from agents.toolboxes.files import FileToolbox


CONFIG = {
    "skill_root": Path("skills/domains/general/root"),
    "provider": "mock",
    "model": "mock",
    "api_key": None,
    "base_url": None,
    "user_id": "check_user",
    "conversation_id": "check_conversation",
    "task_id": "check_task",
    "enhancements": ["todo", "task", "compact"],
    "toolboxes": [FileToolbox()],
}


def build_engine() -> Engine:
    return Engine(
        skill_root=CONFIG["skill_root"],
        provider=CONFIG["provider"],
        model=CONFIG["model"],
        api_key=CONFIG["api_key"],
        base_url=CONFIG["base_url"],
        user_id=CONFIG["user_id"],
        conversation_id=CONFIG["conversation_id"],
        task_id=CONFIG["task_id"],
        toolboxes=CONFIG["toolboxes"],
        enhancements=CONFIG["enhancements"],
    )


def main() -> None:
    assert resolve_provider(None) == DEFAULT_PROVIDER
    assert resolve_model(None) == DEFAULT_MODEL

    engine = build_engine()
    print(engine.chat('/call engine.inspect_skill {"skill":"root"}'))
    print(engine.chat('/call todo.update {"items":[{"id":"1","text":"read skill","status":"in_progress"}]}'))
    print(engine.chat('/call task.create {"subject":"demo task","description":"demo"}'))
    print(engine.chat('/call task.list {}'))
    print("self check finished")


if __name__ == "__main__":
    main()
