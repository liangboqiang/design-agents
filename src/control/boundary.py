from __future__ import annotations


CORE_ENGINE_ACTIONS = (
    "engine.inspect_skill",
    "engine.inspect_action",
    "engine.enter_skill",
    "engine.list_child_skills",
)

HARD_RULES = (
    "Path escape checks stay in tools.",
    "Dangerous shell commands stay blocked in tools.",
    "The model must return JSON for tool use turns.",
    "Task and workspace state transitions stay in runtime stores/capabilities.",
)
