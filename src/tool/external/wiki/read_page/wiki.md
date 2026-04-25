# wiki.read_page

Read one rendered page from the shared wiki store.

## Tool
- `wiki.read_page`

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
- mode: `rule`
- priority: `78`
- rules:
  - `wiki.search`
  - `knowledge_needed`

## Input
```json
{
  "type": "object",
  "properties": {
    "page_id": {
      "type": "string"
    }
  },
  "required": [
    "page_id"
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
Use this tool when a concrete wiki page must be opened after search or direct page lookup.

## Safety
- Reading must be denied when the page is above current permission scope.
