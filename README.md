# MiMo Smart Agent 🧠

**一个基于小米 MiMo-V2.5-Pro 的智能 Agent 框架 — 让 AI 真正帮你干活**

> 本项目是 **Xiaomi MiMo Orbit 百万亿 Token 计划** 的申请项目  
> 展示 MiMo-V2.5-Pro 模型在 Agent 和 Coding 场景下的深度应用

---

## 🌟 项目亮点

- 🤖 **纯 Agent 架构** — 基于 MiMo-V2.5-Pro 的任务规划与执行能力
- 🔧 **工具调用系统** — 支持搜索、文件操作、代码执行、网络请求等多种工具
- 📊 **长上下文处理** — 利用 MiMo 100万 token 上下文窗口处理大型代码库
- 🧩 **插件化设计** — 轻松扩展自定义工具
- 🚀 **生产可用** — CLI + API 双模式，CI/CD 集成友好

## 📋 目录

- [快速开始](#快速开始)
- [使用场景](#使用场景)
- [项目结构](#项目结构)
- [配置说明](#配置说明)
- [API 参考](#api-参考)
- [示例](#示例)
- [申请 MiMo Token](#申请-mimo-token)

---

## 快速开始

### 前置条件

- Python 3.10+
- MiMo API Key（[申请地址](https://platform.xiaomimimo.com)）

### 安装

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/mimo-smart-agent.git
cd mimo-smart-agent

# 安装依赖
pip install -r requirements.txt

# 配置 API Key
cp config/config.yaml.example config/config.yaml
# 编辑 config.yaml，填入你的 MiMo API Key
```

### 一分钟上手

```python
from mimo_agent import MiMoAgent

# 初始化 Agent
agent = MiMoAgent(api_key="your-key", model="MiMo-V2.5-Pro")

# 执行任务
result = agent.run("分析当前目录下的 Python 代码，找出潜在的性能问题")
print(result)
```

---

## 使用场景

### 🔍 智能代码审查
```bash
mimo-agent code-review ./src --format markdown
```

### 📝 文档自动生成
```bash
mimo-agent doc-gen ./src --output docs/api.md
```

### 🐛 Bug 诊断
```bash
mimo-agent debug "项目启动报错" --attach-logs ./logs
```

### 🔄 自动化工作流
```python
# 自定义 Agent 工作流
agent = MiMoAgent(tools=["web_search", "file_ops", "code_exec"])
agent.run("搜索最新的 FastAPI 最佳实践，并更新我们的项目代码")
```

---

## 项目结构

```
mimo-smart-agent/
├── README.md                 # 本文件
├── requirements.txt          # 依赖清单
├── setup.py                  # 安装脚本
├── .gitignore
├── .env.example              # 环境变量模板
├── config/
│   └── config.yaml.example   # 配置文件模板
├── src/
│   ├── __init__.py
│   ├── agent.py              # 核心 Agent 引擎
│   ├── client.py             # MiMo API 客户端
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py           # 工具基类
│   │   ├── web_search.py     # 网络搜索工具
│   │   ├── file_ops.py       # 文件操作工具
│   │   ├── code_exec.py      # 代码执行工具
│   │   └── git_ops.py        # Git 操作工具
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── base.py           # 记忆存储基类
│   │   └── session.py        # 会话记忆管理
│   └── cli.py                # 命令行入口
├── examples/
│   ├── basic_agent.py        # 基础 Agent 示例
│   ├── code_reviewer.py      # 代码审查工具示例
│   └── multi_tool_agent.py   # 多工具协同示例
└── tests/
    ├── test_agent.py
    ├── test_client.py
    └── test_tools.py
```

---

## 配置说明

### 环境变量

```bash
# .env
MIMO_API_KEY=your_api_key_here
MIMO_MODEL=MiMo-V2.5-Pro
MIMO_TEMPERATURE=0.7
MIMO_MAX_TOKENS=8192
```

### 配置文件

```yaml
# config/config.yaml
api:
  key: "${MIMO_API_KEY}"          # 支持环境变量引用
  model: "MiMo-V2.5-Pro"
  temperature: 0.7
  max_tokens: 8192

agent:
  max_steps: 20                   # 最大推理步数
  memory_type: "session"          # session | persistent
  tools_enabled:
    - web_search
    - file_ops
    - code_exec
    - git_ops

logging:
  level: "INFO"
  format: "json"
```

---

## API 参考

### MiMoAgent

```python
class MiMoAgent:
    def __init__(
        self,
        api_key: str,
        model: str = "MiMo-V2.5-Pro",
        tools: list[str] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    )
    
    def run(self, task: str, context: dict | None = None) -> AgentResult:
        """执行任务"""
    
    def run_stream(self, task: str) -> Generator[str, None, AgentResult]:
        """流式执行任务"""
    
    def plan(self, task: str) -> list[Step]:
        """生成任务计划（不执行）"""
```

### MiMoClient

```python
class MiMoClient:
    def chat(self, messages: list[dict], **kwargs) -> dict:
        """普通对话"""
    
    def chat_stream(self, messages: list[dict], **kwargs) -> Generator:
        """流式对话"""
    
    def agent_complete(self, task: str, tools: list[ToolDef], **kwargs) -> dict:
        """Agent 模式完成"""
```

---

## 示例

### 基础用法

```python
# examples/basic_agent.py
from mimo_agent import MiMoAgent
import os

agent = MiMoAgent(
    api_key=os.getenv("MIMO_API_KEY"),
    model="MiMo-V2.5-Pro"
)

# 执行复杂任务
result = agent.run("""
    1. 搜索最新的 Python 3.13 新特性
    2. 分析我们项目是否可以用新特性优化
    3. 生成代码迁移方案
""")

print(f"计划步骤: {result.steps}")
print(f"最终输出: {result.output}")
print(f"Token 消耗: {result.usage}")
```

### 代码审查工具

```bash
# 命令行使用
mimo-agent code-review ./src --format markdown --output review.md
```

### CI/CD 集成

```yaml
# .github/workflows/code-review.yml
name: MiMo Code Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run MiMo Code Review
        uses: your-org/mimo-agent@v1
        with:
          api-key: ${{ secrets.MIMO_API_KEY }}
          target: ./src
```

---

## 申请 MiMo Token

本项目是为 **Xiaomi MiMo Orbit 百万亿 Token 创造者激励计划** 打造的申请项目。

**活动信息：**
- 活动时间：2026年4月28日 ~ 5月28日
- Token 总量：100万亿（100T）
- 最高档位：**Max Plan — 16亿 Credits（价值659元）**
- 申请地址：[100t.xiaomimimo.com](https://100t.xiaomimimo.com/)

**申请技巧：**
- 项目描述越详细，通过率和档位越高
- 附上 GitHub 项目链接作为证明材料
- 说明你使用的 AI 工具和具体场景
- 本项目展示了 MiMo 在 Agent/Coding 场景的深度应用

---

## 许可证

MIT License

---

## 🙏 致谢

- [Xiaomi MiMo](https://mimo.xiaomi.com/) — 提供强大的开源大模型
- [MiMo-V2.5-Pro](https://mimo.mi.com/) — 全球开源第一的 Agent 模型

<p align="center">
  <b>如果本项目对你有帮助，请给一个 ⭐</b>
</p>
