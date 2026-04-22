---
name: agent-build
description: |
  通用治理能力：由当前父 Agent 基于自身配置实例化更小权限、更短提示词预算的子 Agent。
actions:
  - subagent.ask
  - subagent.batch_run
tags:
  - governance
  - agent-build
  - subagent
---

# Agent Build · 子 Agent 构建治理能力

> 这是治理层的通用 Skill。  
> 它只描述一件事：**当前 Agent 如何优雅地构建自己的子 Agent**。

## 默认规则

- 默认继承父 Agent 的基础运行配置
  - provider / model / api_key / base_url
  - registry
  - user_id / conversation_id
  - storage base
- 默认收缩子 Agent 的上下文预算
  - 子 Agent 的 `max_prompt_chars` 应小于父 Agent
- 默认最小化子 Agent 权限
  - 只挂当前子任务所需的最少 Skill / Tool / Capability

## 推荐动作

### `subagent.ask`
用于单个子任务。

### `subagent.batch_run`
用于一批同构、可并行的子任务。

## 使用原则

- 子 Agent 是父 Agent 的执行分身，不是新的顶层入口
- 通用构建逻辑在治理层统一，不在业务 Skill 中重复发明一套
- 业务 Skill 需要批量拆分任务时，应直接引用本 Skill
