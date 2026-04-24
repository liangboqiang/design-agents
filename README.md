# Design Agents VNext

Target architecture migration is in its final cleanup stage. New work must land only in the final roots and names defined by [ARCHITECTURE_CONSTITUTION.md](/e:/A0_Projects/A1_Dynamics_Design_LM/GitLab/design-agents/ARCHITECTURE_CONSTITUTION.md) and [NAMING_CONSTITUTION.md](/e:/A0_Projects/A1_Dynamics_Design_LM/GitLab/design-agents/NAMING_CONSTITUTION.md); do not reintroduce `ctx`, `wiki_store`, `<kind>.md`, or runtime-local prompt and harness files.

This repository now follows a `src/`-first architecture built around the v6.4 single-page truth protocol:

- flat resource layers under `src/skill`, `src/tool`, `src/context`, and `src/agent`
- a protocol index that scans `src/` by folder and treats `page.md` as the entity truth page for that folder
- a unified `SpecRegistry` that assembles skill and agent specs from the protocol index read model
- `SpecRegistry + SurfaceResolver + Prompt + Harness + RuntimeBuilder + Engine` as the main execution spine
- prompt construction lives in `src/prompt/`, turn driving lives in `src/harness/`, and `runtime/engine.py` holds only injected facade operations
- event-driven governance additions with audit trails
- thin agent entrypoints that assemble runtime behavior from `page.md` truth pages

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
- `runtime/builder.py`: the single runtime assembly entrypoint through `RuntimeBuilder`; it keeps prompt and harness objects local and injects narrow turn callables
- `runtime/skill_state.py`: active skill closure and child/ref navigation
- `governance/surface/surface_resolver.py`: final action/tool/skill surface resolution
- `prompt/surface_assembler.py`: text-facing surface assembly
- `prompt/history_compressor.py`: bounded history compaction
- `prompt/knowledge_picker.py`: the injected prompt-layer access path into Wiki knowledge
- `prompt/prompt_assembler.py`: identity/surface/state/expansion/feedback prompt assembly
- `harness/turn_driver.py`: thin loop over narrow callable ports for lifecycle, model calls, parsing, dispatching, and continuation
- `harness/capabilities/`: lifecycle/action extensions that participate in the turn loop without living under runtime
- `wiki/index/impl.py`: persists the registry protocol read model into `src/wiki/store/`
- `wiki/search/impl.py`: searches the persisted wiki catalog
- `runtime/engine.py`: the only external runtime facade; it exposes `chat`, `tick`, and `spawn_child` over injected operations

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
- retired compatibility names are lint errors: `ctx`, `wiki_store`, `<kind>.md`, runtime-local prompt/harness files, `toolbox_hub`, and wiki `runtime_*` shadow pages
