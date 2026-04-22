---
name: core-query
description: |
  通用查询与信息组织母技能。用于把模糊问题转为可执行动作，控制模型
  先理解、再扩展上下文、再调用动作，而不是一上来把所有信息都塞满上下文。
actions:
  - engine.inspect_skill
  - engine.inspect_action
  - engine.list_child_skills
  - files.read_text
  - files.list_dir
---

# Core Query · 查询与理解中枢

> 「先把问题理解清楚，再决定要不要扩展上下文、切换 skill、还是直接调用动作。」

## 设计目的

这个 Skill 是所有高层 Skill 的最小母集之一，负责三件事：

1. 判断当前信息是否足够
2. 在信息不足时按需扩展 Skill / Action 上下文
3. 将自然语言问题转为受控动作调用

---

## 使用纪律

### 1. 先判断，再扩展

不要默认把所有文档和所有技能细节都读进来。

优先顺序：

1. 使用已有摘要回答
2. 不够就 `engine.inspect_action`
3. 再不够就 `engine.inspect_skill`
4. 仍不够才读文件或切换子 Skill

### 2. 只扩展当前真正需要的内容

上下文是预算，不是垃圾桶。

### 3. 描述动作时说业务话，不说实现黑话

优先说：
- 读取说明文档
- 检查当前目录
- 查看某个动作的输入

而不是：
- 调 toolbox
- 调 executor
- 调内部对象

---

## 建议回答流程

| 阶段 | 目标 | 常用动作 |
|------|------|----------|
| 识别 | 识别问题类型 | 无 |
| 扩展 | 按需读取 Skill / Action 细节 | `engine.inspect_*` |
| 执行 | 调用可见动作 | `files.*` 等 |
| 收束 | 生成最终回答 | 无 |

---

## 输出标准

- 简洁
- 可解释
- 不堆提示词术语
- 不把不必要的内部细节暴露给用户
