from __future__ import annotations

from pathlib import Path

from .config import TEXT_EXTENSIONS


class WikiIngestPolicy:
    """Deterministic source selection for shared wiki refresh.

    System sources are intentionally curated so the wiki does not become a raw
    mirror of the repository, but still covers the main self-description layer.
    """

    SYSTEM_PREFIXES = (
        "src/skills/",
        "src/agents/specs/",
        "src/context/templates/",
        "src/tools/",
        "src/runtime/",
        "src/governance/",
        "src/schemas/",
    )

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()

    def relpath(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.project_root).as_posix()
        except ValueError:
            return path.resolve().as_posix()

    def include_system_file(self, path: Path) -> bool:
        rel = self.relpath(path)
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            return False
        if path.name.startswith(".") or "__pycache__" in path.parts:
            return False
        if rel.startswith("data/wiki/") or rel.startswith(".runtime_data/"):
            return False
        if rel.endswith("/__init__.py"):
            return False
        if rel.startswith("tests/"):
            return False
        if rel.endswith(".agent.yaml"):
            return rel.startswith("src/agents/specs/")
        if rel.endswith("SKILL.md"):
            return rel.startswith("src/skills/")
        return rel.startswith(self.SYSTEM_PREFIXES)

    def include_business_file(self, path: Path) -> bool:
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            return False
        return "knowledge" in path.parts

    def include_attachment_file(self, path: Path) -> bool:
        return path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS
