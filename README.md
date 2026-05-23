# GAIA: Game Asset Intelligent Analyst

> 基于 OpenClaw 构建的全栈自进化游戏资产行情分析 Agent 系统。

## 项目简介

GAIA 是一个面向数字经济（游戏资产/Web3商品）的自动化行情采集、分析与决策辅助系统。它扫描多源市场数据，识别品类资金流向与政策面异动，根据历史事件库自动生成三级分析报告（大盘→品类→单品），并通过自省机制持续优化分析逻辑。

## 核心 Pipeline

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  数据采集 Agent   │ ──→ │   分析引擎 Agent  │ ──→ │   输出终端 Agent  │
│ (Trae驱动/定时抓取)│     │ (三级下钻/政策面) │     │ (飞书推送/预警)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         ↓                       ↓                       ↓
    SteamDT/CSQAQ/Buff     历史事件库+品类框架       知识结晶(Skills)
                                                       ↕
                                              ┌─────────────────┐
                                              │   自进化 Agent    │
                                              │ (分析质量自省优化) │
                                              └─────────────────┘
```

## 技术栈

- **运行时**: OpenClaw (Agent 编排 & Cron 调度)
- **数据源**: SteamDT API / CSQAQ API / Buff.163.com
- **采集端**: Trae (自动化数据爬取)
- **模型**: DeepSeek / DeepSeek V4 Flash (Agent 决策核心)
- **输出**: 飞书 Webhook (Bot 推送)
- **代码管理**: GitHub (版本控制 & CI)

## 已有成果

稳定运行 30 天，已产出：

| 模块 | 状态 | 产出 |
|------|------|------|
| 大盘数据采集 | ✅ 每日自动 | 30天连续指数+成交量+成交额 |
| 品类分析 | ✅ 每日自动 | 品类涨跌排行、单品追踪 |
| 预警系统 | ✅ 每15分钟 | 实时异动Push |
| 飞书推送 | ✅ 每日3次 | 开盘/下午/收盘简报 |
| 自进化引擎 | ✅ 持续运行 | 累计自省迭代 23+ 代 |
| 知识结晶 | ✅ 产出Skill | cs2-skin-market 分析框架 |
| 政策面分析 | ✅ 事件驱动 | V社更新解读、市场影响预测 |

### 量化数据

- 日均消耗 Token：约 30 万（单模型 DeepSeek）
- 累计分析报告：30+ 份
- 品类覆盖：7 大品类 / 2000+ 单品
- 市场监控效率提升：从每日手动翻3个网站（约 60 分钟）降至飞书自动接收（3 分钟读完）

## 项目结构

```
gaia/
├── agents/                    # Agent 核心
│   ├── orchestrator.py        # 分析编排引擎（三级下钻）
│   ├── auto_upgrade.py        # 自进化系统（分析质量自省）
│   └── alert_check.py         # 实时预警 Agent
├── piplines/                  # 数据管道
│   ├── fetch_steamdt.py       # SteamDT 大盘数据拉取
│   ├── fetch_csqaq.py         # CSQAQ 品类数据拉取
│   └── collector.py           # Trae 驱动的批量采集器
├── knowledge/                 # 知识库
│   ├── market_events.md       # V社更新历史事件库
│   └── index_history.md       # 指数关键点位参考
├── skills/                    # 固化技能
│   └── cs2-skin-market/       # CS2饰品市场分析 Skill
├── scripts/                   # 辅助工具
│   └── push_feishu_evening.py # 飞书消息推送
└── README.md
```

## 快速开始

```bash
git clone https://github.com/VoON0/gaia.git
cd gaia

# 运行采集
python piplines/fetch_steamdt.py

# 运行分析
python agents/orchestrator.py
```

---

*Built with OpenClaw · Maintained by VoON0*
