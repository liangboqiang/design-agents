---
name: parts-design-root
description: |
  零部件设计域总入口。面向需求理解、参数补全、方案拆解、工作空间管理和结果输出。
children:
  - ../../core/query
  - ../../core/task
  - ../common/requirement_parse
  - ../common/report
  - ../conrod/root
  - ../crankshaft/root
  - ../camshaft/root
refs:
  - ../../core/report
actions:
  - engine.inspect_skill
  - engine.inspect_action
  - engine.enter_skill
  - engine.list_child_skills
  - files.list_dir
  - files.read_text
  - files.write_text
  - shell.run
  - workspace.create
  - workspace.list
  - workspace.run
  - workspace.keep
  - workspace.remove
---

# Parts Design Root · 零部件设计总入口

> 「先识别零件类型，再进入对应子树，不要一开始就让所有设计知识同时进上下文。」

## 设计目标

这个 Root Skill 负责把零部件设计域组织成一棵可导航的 Skill Tree：

- 通用需求解析
- 参数与约束整理
- 连杆设计子域
- 曲轴设计子域
- 报告与结果输出

---

## 进入策略

### 当问题是通用设计需求时

优先进入：
- `common/requirement_parse`
- `core/task`

### 当问题明确指向具体零件时

直接进入：
- `conrod/root`
- `crankshaft/root`

---

## 工作空间原则

零部件设计往往需要独立工作空间，不同任务、不同方案尽量分开。
