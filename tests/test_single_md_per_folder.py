from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def test_single_markdown_per_folder() -> None:
    for folder in (ROOT / "src").rglob("*"):
        if not folder.is_dir() or "__pycache__" in folder.parts:
            continue
        markdowns = [path.name for path in folder.iterdir() if path.is_file() and path.suffix.lower() == ".md"]
        assert len(markdowns) <= 1, f"{folder}: {markdowns}"
