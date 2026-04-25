# engine.inspect_skill

Read the full page for a reachable skill.

## Tool
- `engine.inspect_skill`

## Toolbox
- [[tool/system/runtime]]

## Category
- `engine`
- `read`

## Permission
- level: `1`
- capabilities:
  - `skill.read`

## Activation
- mode: `always`
- priority: `96`

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
Use this tool when the current task needs the full contents of a reachable skill page before taking the next step.

## Safety
- Only reachable skills may be inspected.
- Do not invent hidden skills.
