from __future__ import annotations

from pathlib import Path


class WikiSourcePolicy:
    def include(self, project_root: Path, path: Path) -> tuple[bool, str, list[str]]:
        path = path.resolve()
        project_root = project_root.resolve()
        rel = path.relative_to(project_root).as_posix()

        if any(part in {"__pycache__", ".runtime_data", "data"} for part in path.parts):
            return False, "", []
        if path.name == "__init__.py":
            return False, "", []
        if rel.startswith("tests/"):
            return False, "", []
        if rel.endswith("/SKILL.md"):
            return True, "skill", ["skill", "system"]
        if rel.startswith("src/agents/specs/") and path.suffix in {".yaml", ".yml"}:
            return True, "agent_spec", ["agent", "system"]
        if rel.startswith("src/context/templates/"):
            return True, "context_template", ["context", "system"]
        if rel.startswith("src/tools/") and path.suffix in {".py", ".md", ".json", ".yaml", ".yml"}:
            return True, "tool_source", ["tool", "system"]
        if rel.startswith("src/runtime/") and path.suffix == ".py":
            return True, "runtime_source", ["runtime", "system"]
        if rel.startswith("src/governance/") and path.suffix == ".py":
            return True, "governance_source", ["governance", "system"]
        if rel.startswith("src/schemas/") and path.suffix == ".py":
            return True, "schema_source", ["schema", "system"]
        if "/knowledge/" in rel and path.suffix.lower() in {".md", ".txt", ".json", ".yaml", ".yml", ".csv"}:
            return True, "business_knowledge", ["business", "knowledge"]
        return False, "", []
