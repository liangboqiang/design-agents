# task.get

Read one task from the shared task queue.

## Tool
- `task.get`

## Toolbox
- [[tool/workflow/task]]

## Category
- `task`
- `read`

## Permission
- level: `1`

## Activation
- mode: `manual`
- priority: `60`

## Input
```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "integer"
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
Use this tool when the details of one task are needed.

## Safety
- Only read the managed task queue.
