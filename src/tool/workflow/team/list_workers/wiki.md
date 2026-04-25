# team.list_workers

List registered worker runtimes.

## Tool
- `team.list_workers`

## Toolbox
- [[tool/workflow/team]]

## Category
- `orchestration`
- `read`

## Permission
- level: `3`

## Activation
- mode: `manual`
- priority: `30`

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
Use this tool when the current worker roster is needed.

## Safety
- Only read the managed roster.
