# autonomy.claim_next_task

Claim the next unowned task.

## Tool
- `autonomy.claim_next_task`

## Toolbox
- [[tool/system/autonomy]]

## Category
- `orchestration`

## Permission
- level: `3`

## Activation
- mode: `manual`
- priority: `44`

## Input
```json
{
  "type": "object",
  "properties": {
    "owner": {
      "type": "string"
    }
  },
  "required": [
    "owner"
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
Use this tool for autonomous progress when queued work exists.

## Safety
- Only claim unowned tasks.
