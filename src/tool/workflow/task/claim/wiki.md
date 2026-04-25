# task.claim

Claim an unowned task.

## Tool
- `task.claim`

## Toolbox
- [[tool/workflow/task]]

## Category
- `task`
- `write`

## Permission
- level: `2`

## Activation
- mode: `rule`
- priority: `70`
- rules:
  - `autonomy.claim_next_task`

## Input
```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "integer"
    },
    "owner": {
      "type": "string"
    }
  },
  "required": [
    "task_id",
    "owner"
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
Use this tool when a worker or autonomous runtime claims ownership of a task.

## Safety
- Claim only unowned tasks.
