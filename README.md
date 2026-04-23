# Design Agents VNext

This repository now follows a `src/`-first architecture built around the v6.3 single-page truth protocol:

- flat resource layers under `src/skill`, `src/tool`, `src/ctx`, and `src/agent`
- a unified `GovernanceRegistry` that scans skill, tool, agent, and context truth pages
- `SkillRuntime + SurfaceResolver + ContextAssembler + Harness` as the main execution spine
- event-driven governance additions with audit trails
- thin agent entrypoints that assemble runtime behavior from `agent.md` truth pages

## Layout

```text
src/
  agent/
  ctx/
  domain/
  governance/
  llm/
  runtime/
  schemas/
  shared/
  skill/
  storage/
  tool/
  wiki/
  wiki_store/
tests/
```

## Install

```bash
pip install -r requirements.txt
```

## LLM Config

By default the runtime reads LLM settings from `.env`:

```env
DESIGN_AGENTS_PROVIDER=openai
DESIGN_AGENTS_MODEL=qwen3-coder-plus
DESIGN_AGENTS_API_KEY=your_api_key
DESIGN_AGENTS_BASE_URL=https://your-base-url
```

Explicit constructor arguments or agent/test overrides still win over `.env`.

## Agent Entrypoints

Agent entrypoints live in `src/agent/<name>/`, and each one is backed by an `agent.md` page in the same folder.

- `src/agent/general_chat/`
- `src/agent/parts_design_chat/`
- `src/agent/worker_agent/`
- `src/agent/review_agent/`

Each entrypoint uses the same `runtime.engine.Engine` and differs only by page-driven assembly.

## Running the Thin Test Entrypoints

The chat scripts in `tests/` are now thin wrappers over agent specs:

```bash
python tests/chat_general_engine.py
python tests/chat_parts_design_engine.py
python tests/self_check.py
```

The top-level `CONFIG` dictionaries in those files only override runtime values such as provider, model, and session identifiers.

## Running the Structural Tests

```bash
pytest tests/test_registry.py tests/test_context_assembler.py tests/test_action_surface.py tests/test_refs_activation.py
```

These tests validate:

- registry scanning across skill/tool/agent/context truth pages
- layered prompt assembly
- deduped action surface compilation
- event-driven governance activation for refs/task/workspace expansion

## Key Runtime Components

- `governance/registry.py`: unified scanning and indexing of skill, tool, agent, and context truth pages
- `runtime/skill_runtime.py`: active skill closure and child/ref navigation
- `governance/surface_resolver.py`: final action/tool/skill surface resolution
- `ctx/assembler/context_assembler.py`: identity/surface/state/expansion/feedback prompt assembly
- `runtime/harness.py`: thin loop for lifecycle, model calls, parsing, dispatching, and continuation
- `runtime/engine.py`: the only external runtime entrypoint

## Runtime Data

```text
.runtime_data/
  <user_id>/
    <conversation_id>/
      <task_id>/
        history/
        state/
        workspaces/
        inbox/
        logs/
        workspace_root/
```

## Upgrade Notes

- skill truth lives in `src/skill/**/skill.md`
- agent truth lives in `src/agent/**/agent.md`
- context truth lives in `src/ctx/**/ctx.md`
- shared wiki state lives in `src/wiki_store/`
