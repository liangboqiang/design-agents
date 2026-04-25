# governance.inspect_tool_surface

Inspect the visible tool surface.

## Tool
- `governance.inspect_tool_surface`

## Toolbox
- [[tool/system/inspect]]

## Category
- `governance`
- `read`

## Permission
- level: `2`

## Activation
- mode: `manual`
- priority: `46`

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
Use this tool when governed visibility needs to be inspected directly.

## Safety
- Only report the current governed surface.
