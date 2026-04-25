# team.broadcast

Broadcast a message to all workers.

## Tool
- `team.broadcast`

## Toolbox
- [[tool/workflow/team]]

## Category
- `orchestration`

## Permission
- level: `3`

## Activation
- mode: `manual`
- priority: `27`

## Input
```json
{
  "type": "object",
  "properties": {
    "content": {
      "type": "string"
    }
  },
  "required": [
    "content"
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
Use this tool when all workers need the same coordination message.

## Safety
- Keep broadcast messages concise and relevant.
