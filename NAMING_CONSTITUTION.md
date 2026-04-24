# Naming Constitution

These names are mandatory for new code and documentation.

## Root Names

- Resource roots: `agent`, `skill`, `tool`, `context`
- Knowledge root: `wiki`
- Execution roots: `runtime`, `prompt`, `harness`

## Truth Files

- Every canonical truth page is named `page.md`.
- Runtime-only agent settings live in adjacent extension files such as `runtime.toml`.
- Do not introduce `agent.md`, `skill.md`, `tool.md`, `ctx.md`, `runtime.cfg`, or any other legacy truth filename.

## Runtime Names

- Use `SpecRegistry`, not a second registry naming family.
- Use `SessionState` and `SkillState`, not `SessionRuntime` or `SkillRuntime`.
- Use `PromptAssembler`, `SurfaceAssembler`, and `ReplyParser`, not `ContextAssembler`, `ActionCompiler`, or `ResponseParser`.
- Use `TurnDriver`, `TurnLifecycle`, `TurnPolicy`, `ActionDispatcher`, and `TurnGuard` for harness-layer concepts.
- Use `RuntimeBuilder` as the concrete builder class. Do not reintroduce `EngineBuilder`.

## Forbidden Legacy Names

The following names are retired and must not be introduced in new code, docs, or tests:

- `ctx`
- `wiki_store`
- `<kind>.md`
- `ContextAssembler`
- `ActionCompiler`
- `ResponseParser`
- `SessionRuntime`
- `SkillRuntime`
- `engine_builder`
- `engine_control`
- `engine_ports`
- `control_actions`
- `child_engine_factory`
- `core_participants`
- `wiki/runtime_*`

## Documentation Rule

- README, pages, and tests must describe the current naming constitution, not historical transitional names.
