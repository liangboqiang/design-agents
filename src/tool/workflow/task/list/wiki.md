# task.list

List tasks in the shared task queue.

## Tool
- `task.list`

## Toolbox
- [[tool/workflow/task]]

## Category
- `task`
- `read`

## Permission
- level: `1`

## Activation
- mode: `manual`
- priority: `64`

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
Use this tool when the current task backlog is needed.

## Safety
- Only read the managed task queue.
