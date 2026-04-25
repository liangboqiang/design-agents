# shell.run

Run a shell command inside the current runtime workspace.

## Tool
- `shell.run`

## Toolbox
- [[tool/external/shell]]

## Category
- `shell_exec`
- `high_risk`

## Permission
- level: `4`
- capabilities:
  - `shell.exec`

## Activation
- mode: `manual`
- priority: `20`

## Input
```json
{
  "type": "object",
  "properties": {
    "command": {
      "type": "string"
    }
  },
  "required": [
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
Only expose this tool when the active task requires command execution, repository inspection, or an explicit user request.

## Safety
- Dangerous commands are blocked.
- Prefer read-only commands.
- Never run destructive commands.
