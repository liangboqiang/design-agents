# wiki.read_source

Read the original source text linked from a wiki page.

## Tool
- `wiki.read_source`

## Toolbox
- [[tool/external/wiki]]

## Category
- `wiki_read`
- `read`

## Permission
- level: `2`
- capabilities:
  - `wiki.read`

## Activation
- mode: `rule`
- priority: `60`
- rules:
  - `source_needed`
  - `trace_original_text`

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
Use this tool when the rendered page is not enough and the original source text is required.

## Safety
- Reading must be denied when the page is above current permission scope.
