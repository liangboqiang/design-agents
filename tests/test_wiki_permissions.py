from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tool.builtin.wiki import WikiAdminToolbox, WikiReadOnlyToolbox


def test_reader_toolbox_has_no_write_actions() -> None:
    toolbox = WikiReadOnlyToolbox(workspace_root=ROOT)
    action_ids = [spec.action_id for spec in toolbox.action_specs()]
    assert "wiki_admin.refresh_system" not in action_ids
    assert "wiki_admin.ingest_files" not in action_ids
    assert "wiki_admin.lint" not in action_ids


def test_admin_toolbox_exposes_write_actions() -> None:
    toolbox = WikiAdminToolbox(workspace_root=ROOT)
    action_ids = [spec.action_id for spec in toolbox.action_specs()]
    assert "wiki_admin.refresh_system" in action_ids
    assert "wiki_admin.ingest_files" in action_ids
    assert "wiki_admin.lint" in action_ids
