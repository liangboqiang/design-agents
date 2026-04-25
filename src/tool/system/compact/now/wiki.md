# compact.now

Compact the current conversation history.

## Tool
- `compact.now`

## Toolbox
- [[tool/system/compact]]

## Category
- `governance`
- `write`

## Permission
- level: `2`

## Activation
- mode: `manual`
- priority: `58`

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
Use this tool when context needs to be shortened while preserving useful summary state.

## Safety
- Replace history only through the managed compaction pipeline.
