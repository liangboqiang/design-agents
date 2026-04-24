from __future__ import annotations


class SurfaceAssembler:
    def __init__(self, surface_resolver):
        self.surface_resolver = surface_resolver

    def assemble_surface(self, *, skill_state, action_registry, state_fragments, recent_events):
        return self.surface_resolver.resolve(
            skill_state=skill_state,
            action_registry=action_registry,
            state_fragments=state_fragments,
            recent_events=recent_events,
        )
