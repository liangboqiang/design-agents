from __future__ import annotations

from pathlib import Path

from governance.repo_lint import RepositoryLint


ROOT = Path(__file__).resolve().parents[1]


def test_repository_lint_passes_current_repo() -> None:
    payload = RepositoryLint(ROOT).run()
    assert payload["status"] == "ok"
    assert payload["issue_count"] == 0


def test_repository_lint_flags_new_consolidation_rules(tmp_path: Path) -> None:
    skill_dir = tmp_path / "src" / "skill" / "demo" / "root"
    agent_dir = tmp_path / "src" / "agent" / "demo"
    tool_dir = tmp_path / "src" / "tool" / "demo" / "run"

    skill_dir.mkdir(parents=True)
    agent_dir.mkdir(parents=True)
    tool_dir.mkdir(parents=True)

    (skill_dir / "skill.md").write_text(
        "# Demo Root\n\n## Actions\n- `wiki_admin.refresh_system`\n",
        encoding="utf-8",
    )
    (agent_dir / "agent.md").write_text(
        "# Demo Agent\n\n## Root Skill\n- [[skill/demo/root]]\n\n## LLM\n- `provider=mock`\n",
        encoding="utf-8",
    )
    (tool_dir / "tool.md").write_text(
        "# Demo Run\n\n## Implementation\n- `other.py`\n",
        encoding="utf-8",
    )
    (tool_dir / "other.py").write_text("ACTION_ID = 'demo.run'\n", encoding="utf-8")

    payload = RepositoryLint(tmp_path).run()
    rules = {issue["rule"] for issue in payload["issues"]}

    assert "skill_uses_tool_links" in rules
    assert "agent_runtime_config_not_in_page" in rules
    assert "tool_impl_is_adjacent_impl_py" in rules
