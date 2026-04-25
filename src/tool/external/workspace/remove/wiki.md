# workspace.remove

Remove a managed workspace and optionally complete its task.

## Tool
- `workspace.remove`

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
- priority: `54`
- rules:
  - `workspace.created`
  - `workspace.cleanup_needed`

## Input
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string"
    },
    "complete_task": {
      "type": "boolean"
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
Use this tool when a managed workspace is no longer needed.

## Safety
- Remove only managed runtime workspaces.
