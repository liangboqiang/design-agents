# protocol.review_plan

Approve or reject a submitted plan.

## Tool
- `protocol.review_plan`

## Toolbox
- [[tool/system/protocol]]

## Category
- `orchestration`

## Permission
- level: `3`

## Activation
- mode: `manual`
- priority: `23`

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
    "feedback": {
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
Use this tool when review feedback must be recorded through protocol.

## Safety
- Review only known plan requests.
