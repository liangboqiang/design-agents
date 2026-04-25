# workspace.create

Create an isolated workspace.

## Tool
- `workspace.create`

## Toolbox
- [[tool/external/workspace]]

## Category
- `workspace`
- `write`

## Permission
- level: `3`
- capabilities:
  - `workspace.manage`

## Activation
- mode: `rule`
- priority: `72`
- rules:
  - `task.claimed`
  - `workspace_needed`

## Input
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string"
    },
    "task_id": {
      "type": "integer"
    }
  },
  "required": [
    "name"
  ]
}
```

## Output
```json
{
  "type": "object",
  "properties": {
    "content": {
      "type": "string"
    }
  },
  "additionalProperties": true
}
```

## Context Hint
Use this tool when the task requires a dedicated workspace before files or commands are created.

## Safety
- Create only managed runtime workspaces.
