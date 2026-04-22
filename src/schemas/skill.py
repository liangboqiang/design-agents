from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]


@dataclass(slots=True)
class SkillSpec:
    skill_id: str
    name: str
    description: str
    directory: Path
    markdown_path: Path
    markdown_body: str
    frontmatter: JsonDict
    children: list[str] = field(default_factory=list)
    refs: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

