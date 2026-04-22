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

> 这是治理层的**通用能力 Skill**。  
> 它不限定具体业务域，负责描述“当前 Agent 如何优雅地构建其子 Agent”。

## 能力定位

当前 Agent 在需要拆分任务时，可以基于自身运行上下文构建子 Agent。  
默认规则如下：

- **继承父 Agent 的基础配置**
  - LLM provider / model / api_key / base_url
  - registry
  - user_id / conversation_id
  - storage base
- **收缩子 Agent 的执行上下文**
  - 默认使用更小的 `max_prompt_chars`
  - 只挂载完成当前子任务所需的最小 Skill / Tool / Capability
- **记录父子关系**
  - 子 Agent 应在描述或元信息中标明由哪个父 Agent 构建
  - 子 Agent 只对当前子任务负责，不反向膨胀为新的通用入口

## 适用场景

- 将一个长任务拆成多个短任务并行处理
- 对大量同构材料做批量抽取 / 批量摘要 / 批量检查
- 让子 Agent 在更小上下文中执行单一职责任务

## 推荐动作

### `subagent.ask`
适合单个子任务。

### `subagent.batch_run`
适合一批结构一致、输入独立的子任务并行执行。

## 治理原则

- 子 Agent 是**父 Agent 的执行分身**，不是新的顶层产品入口
- 子 Agent 默认应当**更窄权限、更短提示词、更单一目标**
- 能批量运行的任务，优先使用 `subagent.batch_run`
- 不要为了批处理而给每个子 Agent 挂载不必要的通用工具
