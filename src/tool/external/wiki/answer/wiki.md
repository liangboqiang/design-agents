# wiki.answer

Draft an answer from top wiki pages.

## Tool
- `wiki.answer`

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
- priority: `76`
- rules:
  - `knowledge_needed`
  - `user_requests_wiki_summary`

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
Use this tool when the model should synthesize an answer from wiki matches instead of reading pages one by one.

## Safety
- The answer must stay grounded in visible wiki results.
