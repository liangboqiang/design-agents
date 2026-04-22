from __future__ import annotations

import argparse
import sys
from getpass import getpass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from design_agents.engine import Engine
from design_agents.llm.coding_plan import (
    CODING_PLAN_ANTHROPIC_BASE_URL,
    CODING_PLAN_OPENAI_BASE_URL,
    DEFAULT_CODING_PLAN_MODEL,
)
from design_agents.toolboxes.files import FileToolbox
from design_agents.toolboxes.shell import ShellToolbox


def _default_base_url(provider: str) -> str | None:
    if provider == "openai":
        return CODING_PLAN_OPENAI_BASE_URL
    if provider == "anthropic":
        return CODING_PLAN_ANTHROPIC_BASE_URL
    return None


def _prompt_coding_plan_config(args: argparse.Namespace) -> None:
    if args.provider == "mock" or not sys.stdin.isatty():
        return
    default_base_url = _default_base_url(args.provider)
    if not args.base_url:
        prompt = f"Base URL [{default_base_url}]: "
        entered = input(prompt).strip()
        args.base_url = entered or default_base_url
    if not args.api_key:
        args.api_key = getpass("API Key (sk-sp-...): ").strip() or None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["openai", "anthropic", "mock"], default="openai")
    parser.add_argument("--model", default=DEFAULT_CODING_PLAN_MODEL)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--user-id", default="demo_user")
    parser.add_argument("--conversation-id", default="general_chat")
    parser.add_argument("--task-id", default="task_001")
    parser.add_argument("--enhancement", action="append", default=[])
    args = parser.parse_args()

    _prompt_coding_plan_config(args)

    engine = Engine(
        skill_root=Path("skills/domains/general/root"),
        provider=args.provider,
        model=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
        user_id=args.user_id,
        conversation_id=args.conversation_id,
        task_id=args.task_id,
        toolboxes=[FileToolbox(), ShellToolbox()],
        enhancements=args.enhancement,
    )

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
