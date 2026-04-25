# protocol.respond_shutdown

Approve or reject a shutdown request.

## Tool
- `protocol.respond_shutdown`

## Toolbox
- [[tool/system/protocol]]

## Category
- `orchestration`

## Permission
- level: `3`

## Activation
- mode: `manual`
- priority: `25`

## Input
```json
{
  "type": "object",
  "properties": {
    "request_id": {
      "type": "string"
    },
    "approve": {
      "type": "boolean"
    },
    "reason": {
      "type": "string"
    }
  },
  "required": [
    "request_id",
    "approve"
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
Use this tool when shutdown review is required.

## Safety
- Responses must match known request ids.
