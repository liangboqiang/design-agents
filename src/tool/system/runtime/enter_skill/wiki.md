# engine.enter_skill

Switch the active runtime skill to another reachable skill.

## Tool
- `engine.enter_skill`

## Toolbox
- [[tool/system/runtime]]

## Category
- `engine`
- `navigation`

## Permission
- level: `1`
- capabilities:
  - `skill.enter`

## Activation
- mode: `always`
- priority: `100`

## Input
```json
{
  "type": "object",
  "properties": {
    "skill": {
      "type": "string"
    }
  },
  "required": [
    "skill"
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
Use this tool when another reachable skill is a better fit for the current user request.

## Safety
- Only enter reachable skills.
- Preserve governed skill boundaries.
