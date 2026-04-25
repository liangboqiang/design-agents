# todo.view

Read the current runtime todo list.

## Tool
- `todo.view`

## Toolbox
- [[tool/workflow/todo]]

## Category
- `todo`
- `read`

## Permission
- level: `1`

## Activation
- mode: `manual`
- priority: `66`

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
Use this tool when the current todo state is needed for planning or reporting.

## Safety
- Only read the managed runtime todo store.
