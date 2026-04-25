# wiki_admin.ingest_files

Ingest user-provided files into the shared wiki store.

## Tool
- `wiki_admin.ingest_files`

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
- priority: `12`

## Input
```json
{
  "type": "object",
  "properties": {
    "files": {
      "type": "array"
    }
  },
  "required": [
    "files"
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
Use this tool only when the user explicitly asks to ingest files into the shared wiki store.

## Safety
- File ingestion must respect storage and source boundaries.
