# team.spawn_worker

Spawn a managed worker runtime.

## Tool
- `team.spawn_worker`

## Toolbox
- [[tool/workflow/team]]

## Category
- `orchestration`

## Permission
- level: `3`

## Activation
- mode: `manual`
- priority: `34`

## Input
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string"
    },
    "skill": {
      "type": "string"
    },
    "prompt": {
      "type": "string"
    },
    "tools": {
      "type": "array"
    },
    "enhancements": {
      "type": "array"
    }
  },
  "required": [
    "name",
    "skill",
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
Use this tool when new worker capacity is needed.

## Safety
- Avoid duplicate worker names.
