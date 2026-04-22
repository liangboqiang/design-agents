from __future__ import annotations

from .models import ActionSpec


class ExecutorDispatcher:
    def __init__(self, registry: dict[str, ActionSpec]):
        self.registry = registry

    def dispatch(self, action_id: str, arguments: dict) -> str:
        if action_id not in self.registry:
            return f"Error: unknown action '{action_id}'."
        try:
            return self.registry[action_id].executor(arguments)
        except Exception as exc:  # noqa: BLE001
            return f"Error while executing {action_id}: {exc}"
