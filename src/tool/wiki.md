# Tool Domain

`tool/` is the only tool extension domain in the runtime.

## Scope

- `engine/`
- `registry.py`
- `fs/`
- `shell/`
- `textops/`
- `wiki/`
- `wiki_admin/`
- `workspace/`
- `todo/`
- `task/`
- `compact/`
- `subagent/`
- `team/`
- `protocol/`
- `background/`
- `autonomy/`
- `isolation/`
- `inspect/`
- `refs/`
- `normalize/`
- `db/`
- `kb/`
- `nx/`

## Rules

- Control code does not define LLM-callable tools.
- Tool execution truth lives in Python `ToolSpec` objects.
- Tool contract truth lives in tool `wiki.md`.
- `0 = no_tool`
- `1 = read`
- `2 = write_workspace`
- `3 = orchestration`
- `4 = execution`
- `5 = admin`
