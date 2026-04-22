---
name: general-root
description: |
  通用智能体总入口。适合问答、文件处理、轻量任务执行与多步问题拆解。
children:
  - ../../../core/query
  - ../../../core/task
refs:
  - ../../../core/report
actions:
  - engine.inspect_skill
  - engine.inspect_action
  - engine.enter_skill
  - engine.list_child_skills
  - files.list_dir
  - files.read_text
  - files.write_text
  - files.edit_text
  - shell.run
---

# General Root · 通用执行入口

> 「这是一个通用入口，但不是把所有东西都塞进来，而是把合适的 Skill 打开。」

## 入口定位

这个 Root Skill 负责：

- 面向日常问答与轻执行
- 在需要时进入 `core/query` 做查询整理
- 在需要时进入 `core/task` 做任务拆解
- 通过 `core/report` 收束结果

---

## 当前默认可做的事

| 类别 | 能力 |
|------|------|
| 文件 | 读取、写入、编辑、列目录 |
| 命令 | 在工作区执行安全 shell 命令 |
| 引导 | 查看 Skill / Action 详情，切换子 Skill |

---

## 最佳实践

1. 先用当前摘要回答
2. 再按需扩展 Skill 细节
3. 需要多步时切到 `core/task`
4. 最终要形成清晰输出
