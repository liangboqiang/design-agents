# team.send_message

Send a message to one worker inbox.

## Tool
- `team.send_message`

## Toolbox
- [[tool/workflow/team]]

## Category
- `orchestration`

## Permission
- level: `3`

## Activation
- mode: `manual`
- priority: `28`

## Input
```json
{
  "type": "object",
  "properties": {
    "to": {
      "type": "string"
    },
    "content": {
      "type": "string"
    }
  },
  "required": [
    "to",
    "content"
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
Use this tool when a worker needs follow-up input.

## Safety
- Messages should stay task-relevant.
