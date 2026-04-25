# workspace.keep

Mark a managed workspace as kept.

## Tool
- `workspace.keep`

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
- priority: `58`
- rules:
  - `workspace.created`
  - `workspace.needs_retention`

## Input
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string"
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
Use this tool when the current workspace should be preserved after the task.

## Safety
- Keep only managed runtime workspaces.
