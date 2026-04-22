---
name: wiki-hub-root
description: |
  共享持久化 Wiki 总入口。负责只读查询与管理入口分离，并通过治理层 subagent 能力完成批量抽取。
children:
  - ../ingest
  - ../query
  - ../lint
refs:
  - ../../governance/subagent_engine/root
actions:
  - wiki.search
  - wiki.read_page
  - wiki.read_source
  - wiki.answer
  - wiki_admin.refresh_system
  - wiki_admin.ingest_files
  - wiki_admin.lint
  - subagent.ask
  - subagent.batch_run
tags:
  - wiki
  - knowledge-hub
  - shared-store
---

# Wiki Hub Root

> Wiki 是共享持久化知识中枢，固定存放在 `data/wiki/`。

## 约束

- 普通查询只用 `wiki.*`
- 构建/摄取/校验只用 `wiki_admin.*`
- 系统文件不复制原文，仅生成摘要页并保留 source path / source uri
- 批量抽取通过治理层 subagent 能力完成
