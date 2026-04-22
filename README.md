# Design Agents VNext

This repository now follows a `src/`-first architecture built around:

- flat resource layers under `src/skills`, `src/tools`, `src/context`, and `src/agents`
- a unified `GovernanceRegistry` that scans skills, tools, agent specs, and context assets
- `SkillRuntime + SurfaceResolver + ContextAssembler + Harness` as the main execution spine
- event-driven governance additions with audit trails
- thin agent entrypoints that assemble runtime behavior from `.agent.yaml` specs

## Layout

```text
src/
  agents/
  context/
  governance/
  llm/
  runtime/
  schemas/
  shared/
  skills/
  storage/
  tools/
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

Agent entrypoints live in `src/agents/`, and each one is backed by a YAML spec in `src/agents/specs/`.

- `src/agents/general_chat.py`
- `src/agents/parts_design_chat.py`
- `src/agents/worker_agent.py`
- `src/agents/review_agent.py`

Each entrypoint uses the same `runtime.engine.Engine` and differs only by spec-driven assembly.

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

- registry scanning across skills/tools/agents/context assets
- layered prompt assembly
- deduped action surface compilation
- event-driven governance activation for refs/task/workspace expansion

## Key Runtime Components

- `governance/registry.py`: unified scanning and indexing of skills, tools, agent specs, and context assets
- `runtime/skill_runtime.py`: active skill closure and child/ref navigation
- `governance/surface_resolver.py`: final action/tool/skill surface resolution
- `context/assembler/context_assembler.py`: identity/surface/state/expansion/feedback prompt assembly
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

- legacy top-level `skills/` resources have moved to `src/skills/`
- tests and agent launchers no longer carry a parallel configuration system
- refs activation, tool surface governance, context layering, and runtime audit are now explicit subsystems rather than implicit engine logic
