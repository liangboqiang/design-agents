---
name: crankshaft-root
description: |
  曲轴设计子域入口。面向曲轴设计任务中的需求解析、任务推进、工作空间操作与结果整理。
refs:
  - ../../common/requirement_parse
  - ../../common/report
actions:
  - engine.inspect_skill
  - engine.inspect_action
  - todo.update
  - todo.view
  - task.create
  - task.update
  - task.list
  - files.read_text
  - files.write_text
  - workspace.create
  - workspace.run
---

# Crankshaft Root · 曲轴设计入口

> 「曲轴类问题先稳定需求边界，再拆解执行，不要一开始就直接建模。」

## 推荐工作流

1. 用需求解析 Skill 收束目标与约束
2. 把设计步骤显式拆成 Task
3. 为不同方案开独立 Workspace
4. 最终进入报告 Skill 收束结果
