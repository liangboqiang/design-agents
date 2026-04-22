from __future__ import annotations


def micro_compact(rows: list[dict], *, keep_turns: int) -> list[dict]:
    if keep_turns <= 0 or len(rows) <= keep_turns:
        return rows
    return rows[-keep_turns:]

