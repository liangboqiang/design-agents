---
name: wiki-ingest
description: |
  负责摄取三类知识源：skill 邻接业务资料、系统自描述扫描结果、用户输入与附件。
refs:
  - ../../governance/agent_build/SKILL.md
actions:
  - wiki_admin.refresh_system
  - wiki_admin.ingest_files
tags:
  - wiki
  - ingest
---

# Wiki Ingest · 摄取入口

## 主要动作

### `wiki_admin.refresh_system`
重新扫描并重建共享 wiki 页：

- 所有 Skill 邻接 `knowledge/`
- 系统自描述文件
- Agent / Tool / Runtime / Governance / Schema 关键文本

### `wiki_admin.ingest_files`
摄取用户附件，标准输入为：

```json
{
  "files": [
    {"name": "设计需求.docx", "url": "file:///abs/path/to/file"},
    {"name": "图纸说明.pdf", "url": "https://example.com/spec.pdf"}
  ]
}
```

## 与治理层 Agent Build 的关系

本 Skill 显式引用治理层 `agent_build/SKILL.md`。  
当 wiki 需要对大量系统文件、业务资料或附件执行批量抽取时，应统一复用治理层的 `agent-build` 能力：

- 由当前 wiki Agent 构建更小上下文的子 Agent
- 默认继承父 Agent 基础配置
- 通过 `subagent.batch_run` 执行一批独立抽取任务
- 每个子 Agent 只负责单份或单批材料的抽取与摘要

## 附件治理要求

- 统一标准输入字段为 `files`
- 每个元素包含 `name` 与 `url`
- 用户附件写入共享 wiki catalog 时，来源类型为 `user_file`
