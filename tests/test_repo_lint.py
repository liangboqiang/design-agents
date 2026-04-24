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
    noisy_tool_dir = tmp_path / "src" / "tool" / "demo" / "legacy"
    legacy_runtime_dir = tmp_path / "src" / "runtime" / "harness"
    legacy_wiki_dir = tmp_path / "src" / "wiki" / "runtime_engine"
    retired_ctx_dir = tmp_path / "src" / "ctx" / "demo"
    retired_truth_dir = tmp_path / "src" / "skill" / "legacy_truth"

    skill_dir.mkdir(parents=True)
    agent_dir.mkdir(parents=True)
    tool_dir.mkdir(parents=True)
    noisy_tool_dir.mkdir(parents=True)
    legacy_runtime_dir.mkdir(parents=True)
    legacy_wiki_dir.mkdir(parents=True)
    retired_ctx_dir.mkdir(parents=True)
    retired_truth_dir.mkdir(parents=True)

    (skill_dir / "page.md").write_text(
        "# Demo Root\n\n## Actions\n- `wiki_admin.refresh_system`\n",
        encoding="utf-8",
    )
    (agent_dir / "page.md").write_text(
        "# Demo Agent\n\n## Root Skill\n- [[skill/demo/root]]\n\n## LLM\n- `provider=mock`\n",
        encoding="utf-8",
    )
    (tool_dir / "page.md").write_text(
        "# Demo Run\n\n## Implementation\n- `other.py`\n",
        encoding="utf-8",
    )
    (tool_dir / "other.py").write_text("ACTION_ID = 'demo.run'\n", encoding="utf-8")
    (noisy_tool_dir / "page.md").write_text(
        "# Demo Legacy\n\nCanonical tool page for `demo.legacy`.\n\n## Action ID\n- `demo.legacy`\n\n## Implementation\n- `impl.py`\n",
        encoding="utf-8",
    )
    (noisy_tool_dir / "impl.py").write_text("ACTION_ID = 'demo.legacy'\n", encoding="utf-8")
    (retired_ctx_dir / "ctx.md").write_text("# Retired Context\n", encoding="utf-8")
    (retired_truth_dir / "skill.md").write_text("# Retired Truth\n", encoding="utf-8")

    payload = RepositoryLint(tmp_path).run()
    rules = {issue["rule"] for issue in payload["issues"]}

    assert "skill_uses_tool_links" in rules
    assert "agent_runtime_config_not_in_page" in rules
    assert "tool_impl_is_adjacent_impl_py" in rules
    assert "tool_page_not_protocolized" in rules
    assert "no_legacy_blueprint_paths" in rules
    assert "no_retired_names" in rules
