# Architecture Constitution

This repository follows a `src/`-first architecture with one authoritative execution spine and one authoritative knowledge spine.

## Layer Contracts

- Resource assets live only under `src/agent/`, `src/skill/`, `src/tool/`, and `src/context/`.
- Shared knowledge lives only under `src/wiki/`.
- Runtime orchestration lives only under `src/runtime/`, `src/prompt/`, and `src/harness/`.
- Governance read models and structural policy live only under `src/governance/`.

## Execution Spine

The execution spine is:

- `SpecRegistry`
- `SurfaceResolver`
- `Prompt`
- `Harness`
- `RuntimeBuilder`

The intended flow is:

1. `SpecRegistry` reads protocol truth and assembles runtime-facing specs.
2. `SurfaceResolver` decides the visible governed surface.
3. `Prompt` assembles prompt packets from state, surface, and wiki knowledge.
4. `Harness` runs turn lifecycle, reply parsing, dispatch, and guard boundaries.
5. `RuntimeBuilder` assembles the engine-facing runtime host.

## Knowledge Spine

- `src/wiki/` is the only knowledge hub root.
- `src/wiki/store/` is the only persisted wiki state location.
- Wiki consumes governance read models; it does not define protocol truth independently.

## Engine Boundary

- `runtime/engine.py` is the only external runtime facade.
- `Engine` may hold assembled runtime objects, but construction ownership belongs to `RuntimeBuilder`.
- New prompt or harness implementation details must not be instantiated directly from ad hoc call sites outside the builder.

## Migration Guard

- Do not introduce new roots such as `ctx/` or `wiki_store/`.
- Do not reintroduce prompt or harness implementation files under `src/runtime/`.
- Do not create a second registry, wiki store, or prompt assembly path.
