from __future__ import annotations

from schemas.action import ActionSpec

from .base import Capability


class TodoCapability(Capability):
    capability_name = "todo"
    store_name = "todo.json"

    def bind(self, runtime, capability_lookup=None) -> None:
        super().bind(runtime, capability_lookup)
        if self.runtime.session.read_state_json(self.store_name, None) is None:
            self.runtime.session.write_state_json(self.store_name, {"items": []})

    def _render(self) -> str:
        payload = self.runtime.session.read_state_json(self.store_name, {"items": []})
        lines = []
        for item in payload["items"]:
            icon = {"pending": "[ ]", "in_progress": "[>]", "completed": "[x]"}.get(item["status"], "[?]")
            lines.append(f"{icon} {item['id']}: {item['text']}")
        return "\n".join(lines) or "(empty todo list)"

    def action_specs(self):
        return [
            ActionSpec(
                "todo.update",
                "Update todo list",
                "Update the todo list with pending, in_progress, or completed items.",
                {"type": "object", "properties": {"items": {"type": "array"}}, "required": ["items"]},
                lambda args: self._update(args["items"]),
                "capability.todo",
            ),
            ActionSpec(
                "todo.view",
                "View todo list",
                "Show the current todo list.",
                {"type": "object", "properties": {}},
                lambda args: self._render(),
                "capability.todo",
            ),
        ]

    def _update(self, items: list[dict]) -> str:
        in_progress_count = sum(1 for item in items if item.get("status") == "in_progress")
        if in_progress_count > 1:
            raise ValueError("Only one todo item can be in_progress.")
        normalized = [
            {
                "id": item.get("id") or str(index),
                "text": str(item["text"]),
                "status": str(item.get("status") or "pending"),
            }
            for index, item in enumerate(items, start=1)
        ]
        self.runtime.session.write_state_json(self.store_name, {"items": normalized})
        return self._render()

    def state_fragments(self) -> list[str]:
        return [f"todo:\n{self._render()}"]
