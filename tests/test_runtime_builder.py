from __future__ import annotations

from pathlib import Path

import runtime.builder as builder_module
from governance.registry import SpecRegistry
from runtime.builder import EngineBuildRequest, RuntimeBuilder


ROOT = Path(__file__).resolve().parents[1]


def test_build_bundle_does_not_bootstrap_wiki(monkeypatch) -> None:
    def fail(self) -> None:  # noqa: ANN001
        raise AssertionError("ensure_bootstrap should not run during RuntimeBuilder.build_bundle()")

    monkeypatch.setattr(builder_module.KnowledgeHubService, "ensure_bootstrap", fail)

    bundle = RuntimeBuilder().build_bundle(
        EngineBuildRequest(
            skill_root="skill/general/root",
            registry=SpecRegistry(ROOT),
        )
    )

    assert bundle.knowledge_hub is not None
    assert bundle.agent_spec.root_skill == "skill/general/root"


def test_runtime_builder_injects_dependencies_and_keeps_engine_facade_small(tmp_path: Path) -> None:
    engine = RuntimeBuilder().build_engine(
        EngineBuildRequest(
            skill_root="skill/general/root",
            provider="mock",
            model="mock",
            registry=SpecRegistry(ROOT),
            storage_base=tmp_path,
        )
    )

    assert set(engine.__dict__) == {"_runtime"}
    assert not hasattr(engine, "knowledge_hub")
    assert not hasattr(engine, "action_registry")
    assert engine._runtime.harness.ports.knowledge_picker is engine._runtime.knowledge_picker
    assert not hasattr(engine._runtime.harness, "knowledge_picker")
