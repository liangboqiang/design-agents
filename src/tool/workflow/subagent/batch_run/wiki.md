# subagent.batch_run

Run multiple delegated subagent jobs.

## Tool
- `subagent.batch_run`

## Toolbox
- [[tool/workflow/subagent]]

## Category
- `orchestration`

## Permission
- level: `3`

## Activation
- mode: `manual`
- priority: `32`

## Input
```json
{
  "type": "object",
  "properties": {
    "jobs": {
      "type": "array"
    },
    "max_workers": {
      "type": "integer"
    }
  },
  "required": [
    "jobs"
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
Use this tool when multiple bounded subtasks can run in parallel.

## Safety
- Keep each delegated job concrete and scoped.
