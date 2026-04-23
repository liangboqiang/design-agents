from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATTERNS = (
    "_knowledge" + "_hubs",
    "data/" + "wiki",
    "wiki" + ".refresh",
    "wiki" + ".ingest_files",
    "src/" + "other/",
)


def test_repo_contains_no_legacy_protocol_strings() -> None:
    for path in ROOT.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".pyc"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in PATTERNS:
            assert pattern not in text, f"{pattern} found in {path}"
