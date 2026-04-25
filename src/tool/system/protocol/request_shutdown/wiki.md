# protocol.request_shutdown

Request graceful worker shutdown.

## Tool
- `protocol.request_shutdown`

## Toolbox
- [[tool/system/protocol]]

## Category
- `orchestration`

## Permission
- level: `3`

## Activation
- mode: `manual`
- priority: `26`

## Input
```json
{
  "type": "object",
  "properties": {
    "worker": {
      "type": "string"
    }
  },
  "required": [
    "worker"
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
Use this tool when worker shutdown needs formal coordination.

## Safety
- Target only known workers.
