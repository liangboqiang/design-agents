---
name: parts-design-requirement-parse
description: |
  零部件设计需求解析技能。把用户口语化需求整理成结构化约束、缺失项和确认项。
actions:
  - todo.update
  - todo.view
  - task.create
  - task.list
  - files.write_text
---

# Requirement Parse · 需求解析

> 「先把含糊需求压成结构化约束，再谈设计。」

## 输出结构

至少整理出：

- 零件类型
- 目标对象
- 已知参数
- 缺失参数
- 隐式约束
- 需要用户确认的问题

## 建议动作

1. 用 Todo 先列出解析步骤
2. 复杂场景落成 Task
3. 必要时把结构化结果写成中间文件
