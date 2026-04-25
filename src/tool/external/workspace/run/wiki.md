# workspace.run

Run a shell command inside a named workspace.

## Tool
- `workspace.run`

## Toolbox
- [[tool/external/workspace]]

## Category
- `workspace`
- `execution`

## Permission
- level: `4`
- capabilities:
  - `workspace.exec`

## Activation
- mode: `rule`
- priority: `35`
- rules:
  - `workspace.created`
  - `workspace.command_ran`

## Input
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string"
    },
    "command": {
      "type": "string"
    }
  },
  "required": [
    "name",
    "command"
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
Expose this tool when the task requires executing commands inside a managed workspace.

## Safety
- Only run commands inside a managed workspace.
- Prefer read-only commands when possible.
