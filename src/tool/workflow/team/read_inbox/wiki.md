# team.read_inbox

Read the lead inbox.

## Tool
- `team.read_inbox`

## Toolbox
- [[tool/workflow/team]]

## Category
- `orchestration`
- `read`

## Permission
- level: `3`

## Activation
- mode: `manual`
- priority: `29`

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
Use this tool when lead-side worker responses need inspection.

## Safety
- Only read the managed inbox.
