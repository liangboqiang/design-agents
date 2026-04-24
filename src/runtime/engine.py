from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .builder import RuntimeHost


class Engine:
    """Runtime facade."""

    def __init__(self, *, runtime: RuntimeHost):
        self._runtime = runtime

    def chat(self, message: str, files: list[dict] | None = None) -> str:
        return self._runtime.harness.chat(message, files=files)

    def tick(self) -> str:
        autonomy = self._runtime.capability("autonomy")
        if autonomy is None:
            return "Autonomy not enabled."
        result = autonomy.idle_tick()
        if result and not result.startswith("No unclaimed"):
            return self.chat(f"Auto-claimed task detail:\n{result}")
        return result

    def spawn_child(
        self,
        *,
        skill: str | None,
        enhancements: list[str],
        role_name: str,
        toolboxes: list[str] | None = None,
    ):
        return self._runtime.spawn_child(
            skill=skill,
            enhancements=enhancements or self._runtime.enhancement_names,
            role_name=role_name,
            toolboxes=toolboxes,
        )
