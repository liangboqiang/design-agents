# wiki_admin.refresh_system

Refresh the shared wiki system pages from governed sources.

## Tool
- `wiki_admin.refresh_system`

## Toolbox
- [[tool/external/wiki_admin]]

## Category
- `wiki_admin`
- `admin`

## Permission
- level: `5`
- capabilities:
  - `wiki.admin`

## Activation
- mode: `manual`
- priority: `10`

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
Only expose this tool for explicit wiki refresh or administrative maintenance tasks.

## Safety
- Refresh must stay within governed registry sources.
