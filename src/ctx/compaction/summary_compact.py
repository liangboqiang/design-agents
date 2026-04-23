from __future__ import annotations


def build_summary(rows: list[dict], *, keep_last: int = 12) -> str:
    if not rows:
        return ""
    return "\n".join(f"[{row['role']}] {str(row['content'])[:300]}" for row in rows[-keep_last:])

