---
name: core-task
description: |
  通用任务分解与执行追踪技能。适合多步问题、长链执行、依赖关系明确的任务。
actions:
  - todo.update
  - todo.view
  - task.create
  - task.update
  - task.list
  - task.get
  - task.claim
---

# Core Task · 任务推进与持久化

> 「对话会被压缩，任务状态不能丢。」

## 这个 Skill 解决什么问题

短对话里，模型可以凭记忆推进；长链任务里，不行。

这个 Skill 的目标是：

- 把即时待办和持久任务图区分开
- 让任务在上下文压缩之后仍然存活
- 让子智能体、员工智能体、自主 worker 都能共享任务状态

---

## 双层结构

### 层 1：Todo

适合当前会话内的轻量任务推进。

### 层 2：Task Graph

适合跨轮、跨子智能体、跨 workspace 的持久化任务。

---

## 建议策略

1. 简单任务：先 Todo
2. 明确依赖、多步任务：直接 Task
3. 需要多人协作：Task 为主，Todo 为辅

---

## 注意事项

- 同一时间尽量只保留一个 `in_progress` 的 Todo
- 任务一旦完成，应及时 `task.update(status=completed)`
- 如果任务阻塞，应把阻塞关系写进任务，而不是只写在自然语言里
