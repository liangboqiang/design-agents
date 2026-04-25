# files.diff_text

Show a unified diff between two workspace text files.

## Tool
- `files.diff_text`

## Toolbox
- [[tool/external/fs]]

## Category
- `workspace_io`
- `read`

## Permission
- level: `2`
- capabilities:
  - `workspace.read`

## Activation
- mode: `rule`
- priority: `66`
- rules:
  - `user_requests_diff`
  - `active_skill_requires_comparison`

## Input
```json
{
  "type": "object",
  "properties": {
    "old_path": {
      "type": "string"
    },
    "new_path": {
      "type": "string"
    }
  },
  "required": [
    "old_path",
    "new_path"
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
Use this tool when the task needs a textual comparison between two workspace files.

## Safety
- Both paths must stay inside the workspace root.
