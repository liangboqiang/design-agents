# Design Agents VNext

This repository follows the final `src/`-first architecture defined by [ARCHITECTURE_CONSTITUTION.md](ARCHITECTURE_CONSTITUTION.md) and [NAMING_CONSTITUTION.md](NAMING_CONSTITUTION.md). New work must land only in the final roots and names; do not reintroduce `ctx`, `wiki_store`, `<kind>.md`, or runtime-local prompt and harness files.

This repository follows a single-page truth protocol built around:

- flat resource layers under `src/skill`, `src/tool`, `src/context`, and `src/agent`
- a protocol index that scans `src/` by folder and treats `page.md` as the entity truth page for that folder
- a unified `SpecRegistry` that assembles skill and agent specs from the protocol index read model
- `SpecRegistry + SurfaceResolver + Prompt + Harness + RuntimeBuilder + Engine` as the main execution spine
- prompt construction under `src/prompt/`, turn driving under `src/harness/`, and a minimal external runtime facade in `src/runtime/engine.py`
- event-driven governance additions with audit trails
- thin agent entrypoints assembled from `page.md` truth pages

## Layout

```text
src/
  agent/
  context/
  governance/
  harness/
    capabilities/
    action_dispatcher.py
    reply_parser.py
    turn_driver.py
    turn_guard.py
    turn_lifecycle.py
    turn_policy.py
  llm/
  prompt/
    history_compressor.py
    knowledge_picker.py
    prompt_assembler.py
    prompt_packet.py
    surface_assembler.py
  runtime/
    builder.py
    child_factory.py
    engine.py
    participant_set.py
    service_hub.py
    session_state.py
    skill_state.py
  schemas/
  shared/
  skill/
  storage/
  tool/
  wiki/
    index/
    link/
    render/
    search/
    service/
    store/
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

Agent entrypoints live in `src/agent/<name>/`, and each one is backed by a `page.md` truth page in the same folder.

- `src/agent/general_chat/`
- `src/agent/parts_design_chat/`
- `src/agent/worker_agent/`
- `src/agent/review_agent/`

Each entrypoint uses the same `runtime.engine.Engine` and differs only by page-driven assembly.
Runtime-only agent settings such as `provider`, `model`, and prompt budgets live in adjacent extension files like `runtime.toml`, not in `page.md`.

## Running the Thin Test Entrypoints

The chat scripts in `tests/` are thin wrappers over agent specs:

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
- `runtime/builder.py`: the only runtime assembly entrypoint through `RuntimeBuilder`; it builds the runtime host, installs fault/child/action/turn phases, and returns the engine facade
- `runtime/skill_state.py`: active skill closure and child/ref navigation
- `governance/surface/surface_resolver.py`: final action/tool/skill surface resolution
- `prompt/surface_assembler.py`: text-facing surface assembly
- `prompt/history_compressor.py`: bounded history compaction
- `prompt/knowledge_picker.py`: the injected prompt-layer access path into wiki knowledge
- `prompt/prompt_assembler.py`: identity/surface/state/expansion/feedback prompt assembly
- `harness/turn_driver.py`: thin loop for lifecycle, model calls, parsing, dispatching, and continuation
- `harness/capabilities/`: lifecycle/action extensions that participate in the turn loop without living under runtime
- `wiki/index/impl.py`: persists the registry protocol read model into `src/wiki/store/`
- `wiki/search/impl.py`: searches the persisted wiki catalog
- `runtime/engine.py`: the only external runtime facade; it exposes `chat`, `tick`, and `spawn_child`

## Layer Roles

- `context/` is the asset layer for stable prompt fragments and templates.
- `prompt/` is the context-engineering code layer.
- `wiki/` is the only shared knowledge hub.
- `runtime/` is the runtime host and assembly layer.
- `harness/` is the turn-driving and reply-handling layer.

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
- shared wiki state lives in `src/wiki/store/`
- prompt code lives in `src/prompt/`
- harness code lives in `src/harness/`
- retired compatibility names are lint errors: `ctx`, `wiki_store`, `<kind>.md`, runtime-local prompt/harness files, and wiki `runtime_*` shadow pages
