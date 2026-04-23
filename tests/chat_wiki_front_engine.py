from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from runtime.engine import Engine
from agent.wiki_front_chat import build_engine as build_wiki_front_engine


CONFIG = {
    "provider": "openai",
    "model": "qwen3.5-plus",
    "api_key": "sk-sp-4794e9ca698446a9b42d9079e8474de1",
    "base_url": "https://coding.dashscope.aliyuncs.com/v1",
    "user_id": "demo_user",
    "conversation_id": "wiki_front_chat",
    "task_id": "task_001",
}


def build_engine() -> Engine:
    return build_wiki_front_engine(CONFIG)


def main() -> None:
    engine = build_engine()
    print("wiki_front_chat test harness ready. Enter q to quit.")
    while True:
        try:
            message = input("wiki> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if message.lower() in {"q", "quit", "exit"}:
            break
        print(engine.chat(message))
        print()


if __name__ == "__main__":
    main()
