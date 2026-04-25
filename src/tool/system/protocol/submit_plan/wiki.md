# protocol.submit_plan

Submit a plan for review.

## Tool
- `protocol.submit_plan`

## Toolbox
- [[tool/system/protocol]]

## Category
- `orchestration`

## Permission
- level: `3`

## Activation
- mode: `manual`
- priority: `24`

## Input
```json
{
  "type": "object",
  "properties": {
    "from_worker": {
      "type": "string"
    },
    "plan": {
      "type": "string"
    }
  },
  "required": [
    "from_worker",
    "plan"
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
Use this tool when a worker needs lead review for a plan.

## Safety
- Submit only concrete plan content.
