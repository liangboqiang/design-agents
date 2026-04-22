---
name: wiki-query
description: |
  通过共享 wiki 完成检索、读页、回源与答案综合。
actions:
  - wiki.search
  - wiki.read_page
  - wiki.read_source
  - wiki.answer
tags:
  - wiki
  - query
---

# Wiki Query

## 使用顺序

1. `wiki.search`
2. `wiki.read_page`
3. 必要时 `wiki.read_source`
4. `wiki.answer`
