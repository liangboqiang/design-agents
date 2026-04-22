from __future__ import annotations


class LifecycleManager:
    def __init__(self, participants: list):
        self.participants = participants

    def before_user_turn(self, message: str, files: list[dict] | None = None) -> None:
        for participant in self.participants:
            hook = getattr(participant, "before_user_turn", None)
            if hook is None:
                continue
            try:
                hook(message, files=files)
            except TypeError:
                hook(message)

    def before_model_call(self) -> None:
        for participant in self.participants:
            participant.before_model_call()

    def after_tool_call(self, action_id: str, result: str) -> None:
        for participant in self.participants:
            participant.after_tool_call(action_id, result)

    def state_fragments(self) -> list[str]:
        fragments: list[str] = []
        for participant in self.participants:
            fragments.extend(participant.state_fragments())
        return fragments
