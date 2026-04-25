# subagent.ask

Run one delegated subagent task.

## Tool
- `subagent.ask`

## Toolbox
- [[tool/workflow/subagent]]

## Category
- `orchestration`

## Permission
- level: `3`

## Activation
- mode: `manual`
- priority: `36`

## Input
```json
{
  "type": "object",
  "properties": {
    "prompt": {
      "type": "string"
    },
    "skill": {
      "type": "string"
    },
    "tools": {
      "type": "array"
    },
    "enhancements": {
      "type": "array"
    },
    "toolboxes": {
      "type": "array"
    },
    "role_name": {
      "type": "string"
    }
  },
  "required": [
    "prompt"
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
Use this tool when focused delegation is more efficient than continuing locally.

## Safety
- Delegate only bounded tasks with explicit prompts.
