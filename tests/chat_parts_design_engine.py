from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from runtime.engine import Engine

from agent.parts_design_chat import build_engine as build_parts_design_engine


CONFIG = {
    "provider": "mock",
    "model": "mock",
    "api_key": None,
    "base_url": None,
    "user_id": "demo_user",
    "conversation_id": "parts_chat",
    "task_id": "task_001",
}


def build_engine() -> Engine:
    return build_parts_design_engine(CONFIG)


def main() -> None:
    engine = build_engine()
    print("parts_design_chat test harness ready. Enter q to quit.")
    while True:
        try:
            message = input("parts> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if message.lower() in {"q", "quit", "exit"}:
            break
        print(engine.chat(message))
        print()


if __name__ == "__main__":
    main()
