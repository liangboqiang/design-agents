---
name: wiki-hub-root
description: |
  共享持久化 Wiki 总入口。负责只读查询与管理入口分离，并通过治理层 agent_build 能力完成批量抽取。
children:
  - ../ingest/SKILL.md
  - ../query/SKILL.md
  - ../lint/SKILL.md
refs:
  - ../../governance/agent_build/SKILL.md
actions:
  - wiki.search
  - wiki.read_page
  - wiki.read_source
  - wiki.answer
  - wiki_admin.refresh_system
  - wiki_admin.ingest_files
  - wiki_admin.lint
tags:
  - wiki
  - knowledge-hub
  - shared-store
---

# Wiki Hub Root

> Wiki 是共享持久化知识中枢，固定存放在 `data/wiki/`。

## 约束

- 普通查询只使用 `wiki.*`
- 构建、摄取、校验只使用 `wiki_admin.*`
- 系统文件不复制原文，只生成摘要页并保留 source path / source uri / source hash
- 批量抽取统一通过治理层 `agent_build` 能力完成

## 引用约定

本 Skill 的跨 Skill 引用统一使用显式 `.../SKILL.md` 路径，避免目录与文件写法混杂。
