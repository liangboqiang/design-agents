# Design Agents VNext

This repository now follows a `src/`-first architecture built around the v6.3 single-page truth protocol:

- flat resource layers under `src/skill`, `src/tool`, `src/context`, and `src/agent`
- a protocol index that scans `src/` by folder and treats `page.md` as the entity truth page for that folder
- a unified `SpecRegistry` that assembles skill and agent specs from the protocol index read model
- `SkillState + SurfaceResolver + PromptAssembler + TurnDriver` as the main execution spine
- event-driven governance additions with audit trails
- thin agent entrypoints that assemble runtime behavior from `page.md` truth pages

## Layout

```text
src/
  agent/
  context/
  domain/
  governance/
  harness/
  llm/
  prompt/
  runtime/
  schemas/
  shared/
  skill/
  storage/
  tool/
  wiki/
  wiki/store/
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

Agent entrypoints live in `src/agent/<name>/`, and each one is backed by an `page.md` page in the same folder.

- `src/agent/general_chat/`
- `src/agent/parts_design_chat/`
- `src/agent/worker_agent/`
- `src/agent/review_agent/`

Each entrypoint uses the same `runtime.engine.Engine` and differs only by page-driven assembly.
Runtime-only agent settings such as `provider`, `model`, and prompt budgets live in adjacent truth-extension files like `runtime.toml`, not in `page.md`.

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
python -m pytest
```

These tests validate:

- protocol index summaries and structured metadata
- registry assembly from the protocol index read model
- wiki link-summary rendering
- repo lint guardrails for de-protocolized pages and explicit runtime config ownership

## Key Runtime Components

- `governance/protocol_index/impl.py`: single read model for entity/page indexing, summaries, links, and lightweight section metadata
- `governance/registry/spec_registry.py`: assembly layer that consumes the protocol index read model
- `runtime/skill_state.py`: active skill closure and child/ref navigation
- `governance/surface/surface_resolver.py`: final action/tool/skill surface resolution
- `prompt/prompt_assembler.py`: identity/surface/state/expansion/feedback prompt assembly
- `harness/turn_driver.py`: thin loop for lifecycle, model calls, parsing, dispatching, and continuation
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

- skill truth lives in `src/skill/**/page.md`
- agent truth lives in `src/agent/**/page.md`
- context truth lives in `src/context/**/page.md`
- tool truth lives in `src/tool/**/page.md`
- folders may also contain one non-entity page when the single markdown file is not named after its top-level kind
- shared wiki state lives in `src/wiki/store/`
