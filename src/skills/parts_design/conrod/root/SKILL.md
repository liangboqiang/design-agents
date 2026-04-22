---
name: conrod-root
description: |
  连杆设计子域入口。面向连杆需求澄清、参数整理、方案推进和输出结果。
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

# Conrod Root · 连杆设计入口

> 「连杆类问题先把载荷、尺寸约束、材料与制造边界问清楚。」

## 推荐工作流

1. 调用需求解析 Skill 识别参数缺口
2. 把多步任务落成 Task
3. 为方案创建独立 Workspace
4. 逐步输出中间结果和最终报告
