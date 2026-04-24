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
    assert bundle.context.root_skill_id == "skill/general/root"
    assert not hasattr(bundle, "surface_assembler")
    assert not hasattr(bundle, "action_registry")
    assert not hasattr(bundle, "harness")


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

    assert set(engine.__dict__) == {"_ops"}
    assert not hasattr(engine, "_runtime")
    assert not hasattr(engine, "knowledge_hub")
    assert not hasattr(engine, "action_registry")


def test_turn_ports_are_narrow_runtime_callables(tmp_path: Path) -> None:
    builder = RuntimeBuilder()
    request = EngineBuildRequest(
        skill_root="skill/general/root",
        provider="mock",
        model="mock",
        registry=SpecRegistry(ROOT),
        storage_base=tmp_path,
    )
    runtime = builder.build_bundle(request)
    turn_driver, _ = builder.install_runtime(runtime, request)

    assert set(turn_driver.ports.__dataclass_fields__) == {
        "lifecycle",
        "fault_boundary",
        "emit_event",
        "active_skill_id",
        "history",
        "max_steps",
        "model_name",
        "assemble_surface",
        "build_system_prompt",
        "build_messages",
        "complete_model",
        "parse_reply",
        "dispatch_action",
        "normalize_tool_result",
        "record_audit",
    }
    assert not hasattr(turn_driver.ports, "registry")
    assert not hasattr(turn_driver.ports, "knowledge_hub")
    assert not hasattr(turn_driver.ports, "action_registry")
    assert not hasattr(turn_driver.ports, "knowledge_picker")
