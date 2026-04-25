# wiki.search

Search shared wiki pages.

## Tool
- `wiki.search`

## Toolbox
- [[tool/external/wiki]]

## Category
- `wiki_read`
- `read`

## Permission
- level: `1`
- capabilities:
  - `wiki.read`

## Activation
- mode: `always`
- priority: `82`

## Input
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string"
    },
    "limit": {
      "type": "integer"
    }
  },
  "required": [
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
Use this tool when the task needs knowledge from the shared wiki before answering or planning.

## Safety
- Search results must respect wiki permission filtering.
