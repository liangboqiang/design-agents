from __future__ import annotations

from pathlib import Path

from governance.registry import GovernanceRegistry
from wiki.service import SharedWikiService


ROOT = Path(__file__).resolve().parents[1]


def test_read_page_renders_link_cards_with_store_summaries() -> None:
    service = SharedWikiService(project_root=ROOT, registry=GovernanceRegistry(ROOT))
    service.refresh_system(engine=None)

    body = service.read_page("skill/wiki_hub/ingest")

    assert "- **Refresh Wiki System**" in body
    assert "Refresh the shared wiki index and system summaries." in body
    assert "- **Ingest Wiki Files**" in body
    assert "Ingest user-provided files into the shared wiki store." in body


def test_read_page_renders_inline_links_with_store_summaries() -> None:
    service = SharedWikiService(project_root=ROOT, registry=GovernanceRegistry(ROOT))
    service.refresh_system(engine=None)

    body = service.read_page("wiki/render")

    assert "Wiki Service - Shared wiki adapter backed by `src/wiki/store`." in body
