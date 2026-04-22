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
    "user_id": "demo_user",
    "conversation_id": "general_chat",
    "task_id": "task_001",
    "enhancements": [],
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
    print("general engine ready. Enter q to quit.")
    while True:
        try:
            message = input("general> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if message.lower() in {"q", "quit", "exit"}:
            break
        print(engine.chat(message))
        print()


if __name__ == "__main__":
    main()
