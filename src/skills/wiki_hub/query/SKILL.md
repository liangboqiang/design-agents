---
name: wiki-query
description: |
  通过 wiki 完成检索、读页与答案综合，是知识查询的默认入口。
actions:
  - wiki.search
  - wiki.read_page
  - wiki.answer
tags:
  - wiki
  - query
---

# Wiki Query · 查询入口

## 使用顺序

1. `wiki.search` 先缩小范围
2. `wiki.read_page` 读取命中页
3. `wiki.answer` 让 Wiki 生成归纳答案

## 原则

- 优先使用 wiki 页，不直接把原始资料整段塞进上下文
- 如果需要核验，再回到 raw/source 层做 trace
