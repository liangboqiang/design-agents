# governance.load_refs

Inspect the currently activated refs closure.

## Tool
- `governance.load_refs`

## Toolbox
- [[tool/system/refs]]

## Category
- `governance`
- `read`

## Permission
- level: `2`

## Activation
- mode: `manual`
- priority: `45`

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
Use this tool when active refs closure needs inspection.

## Safety
- Only report currently activated refs.
