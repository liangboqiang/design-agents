from __future__ import annotations

from agents.capabilities.base import Capability
from agents.core.models import ActionSpec
from agents.core.storage import JsonStore


class TodoCapability(Capability):
    capability_name = "todo"

    def bind(self, engine) -> None:
        super().bind(engine)
        self.store = JsonStore(engine.paths.state_dir / "todo.json")
        if not self.store.path.exists():
            self.store.write({"items": []})

    def _render(self) -> str:
        payload = self.store.read({"items": []})
        lines = []
        for item in payload["items"]:
            icon = {"pending": "[ ]", "in_progress": "[>]", "completed": "[x]"}.get(item["status"], "[?]")
            lines.append(f"{icon} {item['id']}: {item['text']}")
        return "\n".join(lines) or "(empty todo list)"

    def action_specs(self):
        return [
            ActionSpec("todo.update", "Update todo list", "更新待办清单，支持 pending / in_progress / completed。", {"type": "object", "properties": {"items": {"type": "array"}}, "required": ["items"]}, lambda args: self._update(args["items"]), "capability.todo", "适合多步任务拆解与执行跟踪。"),
            ActionSpec("todo.view", "View todo list", "查看当前待办清单。", {"type": "object", "properties": {}}, lambda args: self._render(), "capability.todo"),
        ]

    def _update(self, items: list[dict]) -> str:
        in_progress_count = sum(1 for item in items if item.get("status") == "in_progress")
        if in_progress_count > 1:
            raise ValueError("Only one todo item can be in_progress.")
        normalized = [{"id": item.get("id") or str(index), "text": str(item["text"]), "status": str(item.get("status") or "pending")} for index, item in enumerate(items, start=1)]
        self.store.write({"items": normalized})
        return self._render()

    def state_fragments(self) -> list[str]:
        return [f"todo:\n{self._render()}"]
