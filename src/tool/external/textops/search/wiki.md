# textops.search

Search for a substring inside a workspace text file.

## Tool
- `textops.search`

## Toolbox
- [[tool/external/textops]]

## Category
- `text`
- `read`

## Permission
- level: `1`

## Activation
- mode: `manual`
- priority: `72`

## Input
```json
{
  "type": "object",
  "properties": {
    "path": {
      "type": "string"
    },
    "query": {
      "type": "string"
    }
  },
  "required": [
    "path",
    "query"
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
Use this tool to inspect file content without loading the full file.

## Safety
- The path must stay inside the workspace root.
