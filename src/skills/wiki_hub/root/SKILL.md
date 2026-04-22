---
name: wiki-hub-root
description: |
  LLM Wiki 总入口。负责统一摄取业务资料、系统自描述与用户/附件输入，并将 wiki 作为本系统唯一知识中枢。
children:
  - ../ingest
  - ../query
  - ../lint
actions:
  - engine.inspect_skill
  - engine.inspect_action
  - engine.enter_skill
  - engine.list_child_skills
  - wiki.refresh
  - wiki.ingest_files
  - wiki.search
  - wiki.read_page
  - wiki.answer
  - wiki.lint
  - files.read_text
  - files.write_text
tags:
  - wiki
  - knowledge-hub
  - karpathy
---

# Wiki Hub Root · 知识中枢总入口

> Wiki 是**唯一知识中枢**，但不是唯一知识来源。  
> Schema 用于增强秩序、追踪与结构化，不是唯一真相。

## 三类知识源

### 1. 业务资料源
来自每个 Skill 目录下的 `knowledge/` 文件夹。  
这部分面向业务知识、SOP、参数词典、模板、规范、示例等内容。

### 2. 系统自描述源
来自本工程中可扫描的有效系统材料，例如：

- `SKILL.md`
- Agent Spec
- Tool 定义
- Context 模板
- Runtime / Governance / Tool / Agent 的核心源码文本

### 3. 用户输入源
来自用户对话内容，以及附件输入 `files[]`：

```json
[
  {"name": "xxx.pdf", "url": "file:///abs/path/or/http-url"}
]
```

## 原则

- 查询优先走 Wiki 页，而不是直接扫原始资料。
- 原始资料只在 ingest / trace / verify 场景进入主流程。
- 知识页允许野蛮生长，但必须保持可追踪。
- 业务资料、系统自描述、用户附件三类来源都需要在 wiki 中留痕。
