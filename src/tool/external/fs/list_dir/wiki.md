# files.list_dir

List files and directories inside a workspace directory.

## Tool
- `files.list_dir`

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
- priority: `88`

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
Use this tool when the model needs to inspect the shape of the workspace before reading or writing files.

## Safety
- The path must stay inside the workspace root.
