# Governance Agent Build

Skill page for `skill/governance/agent_build`.

## Scope

- 子智能体和批量子任务创建的行为说明归属于本 skill。
- control plane 只保留运行代码，不再保留只有 `page.md` 的治理说明页。
- 构建 child agent 时应继承父运行时的 registry、LLM 配置、存储根与可见工具箱边界。

## Tools
- [[tool/subagent/ask]]
- [[tool/subagent/batch_run]]
