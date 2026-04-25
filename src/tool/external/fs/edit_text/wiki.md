# files.edit_text

Replace one exact text fragment inside an existing workspace file.

## Tool
- `files.edit_text`

## Toolbox
- [[tool/external/fs]]

## Category
- `workspace_io`
- `write`

## Permission
- level: `2`
- capabilities:
  - `workspace.write`

## Activation
- mode: `rule`
- priority: `68`
- rules:
  - `user_requests_targeted_edit`
  - `active_skill_requires_patch`

## Input
```json
{
  "type": "object",
  "properties": {
    "path": {
      "type": "string"
    },
    "old_text": {
      "type": "string"
    },
    "new_text": {
      "type": "string"
    }
  },
  "required": [
    "path",
    "old_text",
    "new_text"
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
Use this tool when the model needs a small, targeted edit while keeping surrounding content intact.

## Safety
- The path must stay inside the workspace root.
- The old text must match exactly before editing.
