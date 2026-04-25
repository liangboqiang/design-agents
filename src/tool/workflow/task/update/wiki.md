# task.update

Update task status, owner, or dependencies.

## Tool
- `task.update`

## Toolbox
- [[tool/workflow/task]]

## Category
- `task`
- `write`

## Permission
- level: `2`

## Activation
- mode: `rule`
- priority: `66`
- rules:
  - `task.claimed`
  - `task.blocked`

## Input
```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "integer"
    },
    "status": {
      "type": "string"
    },
    "owner": {
      "type": "string"
    },
    "add_blocked_by": {
      "type": "array"
    },
    "remove_blocked_by": {
      "type": "array"
    }
  },
  "required": [
    "task_id"
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
Use this tool when tracked work changes state.

## Safety
- Only update managed task fields.
