# engine.list_child_skills

List the direct child skills of the current active skill.

## Tool
- `engine.list_child_skills`

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
- priority: `94`

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
Use this tool when the model needs to see which child skills are directly reachable from the current skill.

## Safety
- Only list governed child skills.
