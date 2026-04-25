# task.create

Create a task in the shared task queue.

## Tool
- `task.create`

## Toolbox
- [[tool/workflow/task]]

## Category
- `task`
- `write`

## Permission
- level: `2`

## Activation
- mode: `manual`
- priority: `68`

## Input
```json
{
  "type": "object",
  "properties": {
    "subject": {
      "type": "string"
    },
    "description": {
      "type": "string"
    },
    "blocked_by": {
      "type": "array"
    }
  },
  "required": [
    "subject"
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
Use this tool when new tracked work must be created.

## Safety
- Keep task subjects concise and explicit.
