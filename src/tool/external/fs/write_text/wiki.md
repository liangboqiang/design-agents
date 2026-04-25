# files.write_text

Write text into a file inside the current runtime workspace.

## Tool
- `files.write_text`

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
- priority: `70`
- rules:
  - `user_requests_file_creation`
  - `active_skill_outputs_report`

## Input
```json
{
  "type": "object",
  "properties": {
    "path": {
      "type": "string"
    },
    "content": {
      "type": "string"
    }
  },
  "required": [
    "path",
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
Use this tool when the user asks for a generated file, report, code artifact, or persistent workspace output.

## Safety
- Do not overwrite files unless the request or active skill implies an update.
- Prefer creating new files when uncertain.
