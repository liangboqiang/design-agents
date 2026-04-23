from __future__ import annotations


class SurfaceAssembler:
    def __init__(self, surface_resolver):
        self.surface_resolver = surface_resolver

    def compile_surface(self, *, skill_runtime, action_registry, state_fragments, recent_events):
        return self.surface_resolver.resolve(
            skill_runtime=skill_runtime,
            action_registry=action_registry,
            state_fragments=state_fragments,
            recent_events=recent_events,
        )


ActionCompiler = SurfaceAssembler
