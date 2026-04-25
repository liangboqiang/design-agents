# background.run

Run a shell command in the background.

## Tool
- `background.run`

## Toolbox
- [[tool/system/background]]

## Category
- `execution`
- `high_risk`

## Permission
- level: `4`

## Activation
- mode: `manual`
- priority: `18`

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
Use this tool when long-running command execution should not block the current turn.

## Safety
- Run only inside the managed workspace.
