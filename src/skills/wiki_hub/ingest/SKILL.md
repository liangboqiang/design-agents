---
name: wiki-ingest
description: |
  负责摄取三类知识源：skill 邻接业务资料、系统自描述扫描结果、用户输入与附件。
refs:
  - ../../governance/agent_build/SKILL.md
actions:
  - wiki.refresh
  - wiki.ingest_files
  - files.read_text
tags:
  - wiki
  - ingest
---

# Wiki Ingest · 摄取入口

## 主要动作

### `wiki.refresh`
重新扫描：

- 所有 Skill 邻接 `knowledge/`
- 系统自描述文件
- Agent / Tool / Runtime / Governance 关键文本

### `wiki.ingest_files`
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

本 Skill **显式引用**治理层 `agent_build/SKILL.md`。  
当 wiki 需要对大量系统文件、业务资料或附件执行批量抽取时，应优先复用治理层的 `agent-build` 能力：


## 附件治理要求

- 统一标准输入字段为 `files`
- 每个元素包含 `name` 与 `url`
- 先落盘到运行态附件目录，再入 wiki
- wiki 页必须记录来源类型为 `user_attachment`
