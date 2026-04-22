# Design Agents

一个基于 `Skill + Action + Toolbox` 的轻量 Agent Engine。

当前项目已经统一为 **DashScope Coding Plan** 接入方案：
- API Key 使用 `sk-sp-...`
- OpenAI 协议 Base URL 使用 `https://coding-intl.dashscope.aliyuncs.com/v1`
- Anthropic 协议 Base URL 使用 `https://coding-intl.dashscope.aliyuncs.com/apps/anthropic`
- 默认模型使用 `qwen3-coder-plus`

## 安装

```bash
pip install -r requirements.txt
```

## 配置

推荐复制仓库根目录下的 `.env.example`，并填写你的套餐密钥：

```env
AGENTS_PROVIDER=openai
AGENTS_MODEL=qwen3-coder-plus
AGENTS_API_KEY=sk-sp-your-coding-plan-key
AGENTS_BASE_URL=https://coding-intl.dashscope.aliyuncs.com/v1
```

## 快速开始

通用对话入口，OpenAI 兼容协议：

```bash
python tests/chat_general_engine.py --provider openai --model qwen3-coder-plus --base-url https://coding-intl.dashscope.aliyuncs.com/v1 --api-key YOUR_SK_SP_KEY
```

零部件设计入口，Anthropic 兼容协议：

```bash
python tests/chat_parts_design_engine.py --provider anthropic --model qwen3-coder-plus --base-url https://coding-intl.dashscope.aliyuncs.com/apps/anthropic --api-key YOUR_SK_SP_KEY
```

离线模式：

```bash
python tests/chat_general_engine.py --provider mock --model mock
```

自检：

```bash
python tests/self_check.py
```

## 交互输入模式

如果你不想把密钥写在命令行里，可以直接启动脚本：

```bash
python tests/chat_general_engine.py
```

脚本会提示你输入：
- `Base URL`
- `API Key (sk-sp-...)`

## Engine 示例

```python
from pathlib import Path

from agents.engine import Engine
from agents.toolboxes.files import FileToolbox
from agents.toolboxes.shell import ShellToolbox

engine = Engine(
    skill_root=Path("skills/domains/general/root"),
    provider="openai",
    model="qwen3-coder-plus",
    api_key="YOUR_SK_SP_KEY",
    base_url="https://coding-intl.dashscope.aliyuncs.com/v1",
    user_id="u01",
    conversation_id="c01",
    task_id="t01",
    toolboxes=[FileToolbox(), ShellToolbox()],
    enhancements=["todo", "subagent", "compact", "task", "background"],
)

print(engine.chat("请先读取当前目录并告诉我有哪些文件。"))
```

## 能力结构

- `skills/`: 技能树
- `agents/core/`: 核心调度、prompt、skill catalog、history
- `agents/llm/`: Coding Plan OpenAI / Anthropic / mock 客户端
- `agents/toolboxes/`: 文件、shell、MCP stdio 工具箱
- `agents/capabilities/`: todo、task、subagent、background、workspace 等增强能力
- `tests/`: 对话入口和离线自检脚本

## 增强能力

默认全部按需开启，可选项包括：

- `todo`
- `subagent`
- `compact`
- `task`
- `background`
- `team`
- `protocol`
- `autonomy`
- `workspace`
- `isolation`

## 运行时目录

```text
.runtime_data/
  <user_id>/
    <conversation_id>/
      <task_id>/
        history/
        state/
        workspaces/
        inbox/
        logs/
        workspace_root/
```

## Skill 说明

每个 Skill 都是一个目录，目录下必须有 `SKILL.md`。

示例：

```markdown
---
name: general-root
description: 通用问答与任务执行总入口
children:
  - ../../../core/query
  - ../../../core/task
refs:
  - ../../../core/report
actions:
  - engine.inspect_skill
  - engine.enter_skill
  - files.read_text
---
```

## 说明

这个项目现在不再围绕旧式 OpenAI 官方直连配置做兜底兼容，而是明确以 **Coding Plan 专属 API Key + Base URL** 为唯一推荐方案。
