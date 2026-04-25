# todo.update

Update the runtime todo list.

## Tool
- `todo.update`

## Toolbox
- [[tool/workflow/todo]]

## Category
- `todo`
- `write`

## Permission
- level: `2`

## Activation
- mode: `manual`
- priority: `62`

## Input
```json
{
  "type": "object",
  "properties": {
    "items": {
      "type": "array"
    }
  },
  "required": [
    "items"
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
Use this tool when the plan or task list needs to be updated.

## Safety
- At most one item may be in progress.
