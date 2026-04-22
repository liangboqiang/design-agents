from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from runtime.engine import Engine

from agents.general_chat import build_engine as build_general_engine


CONFIG = {
    "provider": "mock",
    "model": "mock",
    "api_key": None,
    "base_url": None,
    "user_id": "check_user",
    "conversation_id": "check_conversation",
    "task_id": "check_task",
}


def build_engine() -> Engine:
    return build_general_engine(CONFIG)


def main() -> None:
    engine = build_engine()
    commands = [
        '/call engine.inspect_skill {"skill":"general/root"}',
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
