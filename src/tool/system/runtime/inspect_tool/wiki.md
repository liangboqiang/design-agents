# engine.inspect_tool

Inspect the schema and description for one currently visible tool.

## Tool
- `engine.inspect_tool`

## Toolbox
- [[tool/system/runtime]]

## Category
- `engine`
- `read`

## Permission
- level: `1`
- capabilities:
  - `tool.read`

## Activation
- mode: `always`
- priority: `95`

## Input
```json
{
  "type": "object",
  "properties": {
    "tool": {
      "type": "string"
    }
  },
  "required": [
    "tool"
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
Use this tool when the model needs the exact schema or description for a visible tool before calling it.

## Safety
- Only visible tools may be inspected.
- Do not treat hidden tools as callable.
