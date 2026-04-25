# files.read_text

Read a text file from the current runtime workspace.

## Tool
- `files.read_text`

## Toolbox
- [[tool/external/fs]]

## Category
- `workspace_io`
- `read`

## Permission
- level: `1`
- capabilities:
  - `workspace.read`

## Activation
- mode: `always`
- priority: `90`

## Input
```json
{
  "type": "object",
  "properties": {
    "path": {
      "type": "string"
    }
  },
  "required": [
    "path"
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
Use this tool when the user asks to inspect a file, review source text, or load workspace-local material.

## Safety
- The path must stay inside the workspace root.
- Do not infer hidden files.
