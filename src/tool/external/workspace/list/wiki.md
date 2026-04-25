# workspace.list

List current managed workspaces.

## Tool
- `workspace.list`

## Toolbox
- [[tool/external/workspace]]

## Category
- `workspace`
- `read`

## Permission
- level: `3`
- capabilities:
  - `workspace.read`

## Activation
- mode: `rule`
- priority: `62`
- rules:
  - `workspace_needed`
  - `workspace.created`

## Input
```json
{
  "type": "object",
  "properties": {}
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
Use this tool when the model needs to inspect existing managed workspaces.

## Safety
- Only list managed runtime workspaces.
