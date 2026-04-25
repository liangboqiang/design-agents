# governance.normalize_tool_result

Normalize an arbitrary tool result into a compact JSON payload.

## Tool
- `governance.normalize_tool_result`

## Toolbox
- [[tool/system/normalize]]

## Category
- `governance`
- `write`

## Permission
- level: `2`

## Activation
- mode: `manual`
- priority: `42`

## Input
```json
{
  "type": "object",
  "properties": {
    "result": {}
  },
  "required": [
    "result"
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
Use this tool when a tool result must be made easier to consume downstream.

## Safety
- Only normalize provided input.
