# background.check

Check the status of a background task.

## Tool
- `background.check`

## Toolbox
- [[tool/system/background]]

## Category
- `execution`
- `read`

## Permission
- level: `3`

## Activation
- mode: `manual`
- priority: `40`

## Input
```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string"
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
Use this tool when background task status or output is needed.

## Safety
- Only inspect managed background tasks.
