from __future__ import annotations


class StateLayer:
    def build(self, history_rows: list[dict], state_fragments: list[str]) -> list[tuple[str, str]]:
        history_body = "\n".join(
            f"- {row['role']}: {str(row['content'])[:200]}"
            for row in history_rows[-8:]
        ) or "- (empty)"
        state_body = "\n".join(state_fragments) or "(no extra state)"
        return [
            ("Working State", state_body),
            ("Recent History", history_body),
        ]
