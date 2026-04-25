# textops.preview_replace

Preview a one-shot text replacement without writing the file.

## Tool
- `textops.preview_replace`

## Toolbox
- [[tool/external/textops]]

## Category
- `text`
- `write`

## Permission
- level: `2`

## Activation
- mode: `rule`
- priority: `64`
- rules:
  - `user_requests_targeted_edit`

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
Use this tool when the model needs to compare before and after text safely.

## Safety
- The path must stay inside the workspace root.
- This tool must not write changes.
