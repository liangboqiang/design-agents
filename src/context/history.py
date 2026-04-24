from __future__ import annotations


def micro_compact(rows: list[dict], *, keep_turns: int) -> list[dict]:
    if keep_turns <= 0 or len(rows) <= keep_turns:
        return rows
    return rows[-keep_turns:]


def build_summary(rows: list[dict], *, keep_last: int = 12) -> str:
    if not rows:
        return ""
    return "\n".join(f"[{row['role']}] {str(row['content'])[:300]}" for row in rows[-keep_last:])


class HistoryCompressor:
    @staticmethod
    def micro_compact(rows: list[dict], *, keep_turns: int) -> list[dict]:
        return micro_compact(rows, keep_turns=keep_turns)

    @staticmethod
    def build_summary(rows: list[dict], *, keep_last: int = 12) -> str:
        return build_summary(rows, keep_last=keep_last)
