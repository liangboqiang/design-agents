from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.engine import Engine
from agents.toolboxes.files import FileToolbox
from agents.toolboxes.shell import ShellToolbox


CONFIG = {
    "skill_root": Path("skills/domains/general/root"),
    "provider": "openai",
    "model": "qwen3.5-plus",
    "api_key": "sk-sp-4794e9ca698446a9b42d9079e8474de1",
    "base_url": "https://coding.dashscope.aliyuncs.com/v1",
    "user_id": "check_user",
    "conversation_id": "check_conversation",
    "task_id": "check_task",
    "enhancements": ["todo", "task", "compact"],
    "toolboxes": [FileToolbox(), ShellToolbox()],
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
    engine = build_engine()
    commands = [
        '/call engine.inspect_skill {"skill":"root"}',
        '/call todo.update {"items":[{"id":"1","text":"read skill","status":"in_progress"}]}',
        '/call task.create {"subject":"demo task","description":"demo"}',
        "/call task.list {}",
    ]
    for command in commands:
        print(f"> {command}")
        print(engine.chat(command))
    print("self check finished")


if __name__ == "__main__":
    main()
