from __future__ import annotations

from schemas.event import Event

from .dedupe import dedupe_strings


class ActivationPolicy:
    def resolve(
        self,
        *,
        active_skill_id: str,
        base_skill_ids: list[str],
        recent_events: list[Event],
        state_fragments: list[str],
    ) -> tuple[list[str], list[str]]:
        activated = list(base_skill_ids)
        notes: list[str] = []
        event_names = {event.name for event in recent_events}
        state_blob = "\n".join(state_fragments).lower()

        if len(base_skill_ids) > 1:
            activated.extend(["governance/refs_bridge", "governance/tool_surface"])
            notes.append("Refs closure activated governance bridge skills.")

        if "compact.performed" in event_names or "compacted summary" in state_blob:
            activated.append("governance/compact_guard")
            notes.append("Compact guard activated after compaction signal.")

        if "task.blocked" in event_names or "blocked_by" in state_blob:
            activated.append("governance/task_governance")
            notes.append("Task governance activated because blocked work was detected.")

        if any(name.startswith("workspace.") for name in event_names):
            activated.append("governance/workspace_governance")
            notes.append("Workspace governance activated because workspace events were emitted.")

        if any(name.startswith("protocol.") for name in event_names):
            activated.append("governance/protocol_governance")
            notes.append("Protocol governance activated because protocol events were emitted.")

        if any(name.startswith("tool.error") for name in event_names):
            activated.extend(["governance/tool_surface", "governance/workspace_governance"])
            notes.append("Tool surface governance activated because a tool error was observed.")

        return dedupe_strings(activated), dedupe_strings(notes)

