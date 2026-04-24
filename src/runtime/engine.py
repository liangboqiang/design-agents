from __future__ import annotations


class Engine:
    """Runtime facade."""

    def __init__(self, *, chat, tick, spawn_child):  # noqa: ANN001
        self._ops = (chat, tick, spawn_child)

    def chat(self, message: str, files: list[dict] | None = None) -> str:
        return self._ops[0](message, files=files)

    def tick(self) -> str:
        return self._ops[1]()

    def spawn_child(
        self,
        *,
        skill: str | None,
        enhancements: list[str],
        role_name: str,
        toolboxes: list[str] | None = None,
    ):
        return self._ops[2](
            skill=skill,
            enhancements=enhancements,
            role_name=role_name,
            toolboxes=toolboxes,
        )
