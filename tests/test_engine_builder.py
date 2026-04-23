from __future__ import annotations

from pathlib import Path

import runtime.engine_builder as engine_builder_module
from governance.registry import GovernanceRegistry
from runtime.engine_builder import EngineBuildRequest, EngineBuilder


ROOT = Path(__file__).resolve().parents[1]


def test_build_bundle_does_not_bootstrap_wiki(monkeypatch) -> None:
    def fail(self) -> None:  # noqa: ANN001
        raise AssertionError("ensure_bootstrap should not run during EngineBuilder.build_bundle()")

    monkeypatch.setattr(engine_builder_module.KnowledgeHubService, "ensure_bootstrap", fail)

    bundle = EngineBuilder().build_bundle(
        EngineBuildRequest(
            skill_root="skill/general/root",
            registry=GovernanceRegistry(ROOT),
        )
    )

    assert bundle.knowledge_hub is not None
    assert bundle.agent_spec.root_skill == "skill/general/root"
