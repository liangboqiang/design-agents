# Design Agents

`agents/` is a lightweight skill-driven agent engine built around `Skill + Action + Toolbox`.

## Install

```bash
pip install -r requirements.txt
```

## Environment Config

Copy `.env.example` to `.env` and fill in these values when you want a real LLM backend:

```env
DESIGN_AGENTS_PROVIDER=openai
DESIGN_AGENTS_MODEL=qwen3-coder-plus
DESIGN_AGENTS_API_KEY=your_api_key
DESIGN_AGENTS_BASE_URL=https://your-base-url
```

`Engine(...)` resolves LLM config from a single place:

- Explicit `provider / model / api_key / base_url` arguments win.
- Missing arguments fall back to `.env`.
- `mock` does not require `api_key` or `base_url`.

## Engine Usage

Default from `.env`:

```python
from pathlib import Path

from agents.engine import Engine

engine = Engine(skill_root=Path("skills/domains/general/root"))
```

Explicit override:

```python
from pathlib import Path

from agents.engine import Engine
from agents.toolboxes.files import FileToolbox
from agents.toolboxes.shell import ShellToolbox

engine = Engine(
    skill_root=Path("skills/domains/general/root"),
    provider="openai",
    model="gpt-4.1-mini",
    api_key="your_api_key",
    base_url="https://your-base-url/v1",
    user_id="u01",
    conversation_id="c01",
    task_id="t01",
    toolboxes=[FileToolbox(), ShellToolbox()],
    enhancements=["todo", "task", "compact", "background"],
)
```

## Test Scripts

The test scripts are intentionally simple application entrypoints. Edit the top-level `CONFIG` in each file, then run it directly:

```bash
python tests/chat_general_engine.py
python tests/chat_parts_design_engine.py
python tests/self_check.py
```

Notes:

- `tests/chat_general_engine.py` uses `skills/domains/general/root`.
- `tests/chat_parts_design_engine.py` uses `skills/domains/parts_design/root`.
- `tests/self_check.py` runs a fixed mock self-check sequence.
- With the default mock configs, all three scripts run without `.env`.

## Layout

- `skills/`: skill tree
- `agents/core/`: prompt assembly, dispatching, history, storage
- `agents/llm/`: LLM clients and config resolution
- `agents/toolboxes/`: workspace file and shell toolboxes
- `agents/capabilities/`: optional capability modules
- `tests/`: simple engine entry scripts

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
