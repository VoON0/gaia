import sys; sys.stdout.reconfigure(encoding='utf-8')
import json, time
from datetime import datetime
from shared.feishu import push_feishu

# ===== 正文内容 =====

tz_bj = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time() + 8*3600))

msg = f"""📊 CS2 下午简报 | {tz_bj}

━━━ 大盘概览 ━━━
📉 饰品指数: 1729.69 (-0.65%)
📈 租赁指数: 488.49 (+0.14%)
📉 百元主战: 3097.38 (-0.38%)
📉 手套指数: 718.39 (-1.04%)
📈 挂件指数: 320.13 (+0.57%)

涨跌分布: 🔴上涨17.6% | ⚪平盘44.5% | 🔵下跌38.0%
贪婪指数: 86.2 (低迷)

━━━ 时K线+T+7 判断 ━━━
饰品指数日跌0.65%，连续阴跌趋势。30日维度所有主要指数均为负值，大盘处中期下行通道。百元主战-0.38%相对抗跌，说明资金在向核心流通品聚集避险。挂件指数+0.57%逆势上涨，小品类资金流入。(结合品类报告：P2000、挂件连续抗跌，与大盘数据一致)

个人判断：大盘短期偏空，但下跌斜率收窄，关注1720支撑位。未出现恐慌抛售。

━━━ 关注品类 ━━━
🔥 逆势上涨:
- P2000 +1.51% (7日+1.12%)
- 挂件 +0.87% (7日+1.64%)
- 折叠刀 +0.44% (7日+4.63%☆)

📉 承压品种:
- 驾驶手套 -2.17% (7日-7.11%)
- 手部束带 -2.20% (7日-6.04%)
- 血猎手套 -1.56% (7日-10.97%⚠️)
- AK-47 -0.30% (7日-0.89%) 大盘晴雨表偏弱

品类交叉验证：品类报告显示AUG三角战术+8.47%、加利尔AR金属榨汁机+18.75%等低价步枪逆势异动，与大盘数据中P2000领涨方向一致，资金在向低价流通品迁移。

━━━ 热门异动 ━━━
🏆 热度飙升: AK-47安全网, M4A1氮化处理, AK翡翠细条纹
📈 涨幅TOP: 棱彩2号箱(+585%), 2020RMR胶囊(+500%)
📉 跌幅TOP: 地平线箱(-505%), 20周年箱(-500%), 光谱箱(-469%)

━━━ GitHub AI 热榜 ━━━
🔥 本周AI方向 30个热门(Stars>100)
Top 5:
1. smallcode — 4B小模型AI coding agent (730⭐)
2. Claude-Mythos-AI — Claude角色扮演客户端
3. Claude-Code-Design-AI — 截图→React AI设计(451⭐)
4. TradingAgents-astock — 大A多Agent投研(402⭐)
5. orthrus — 双视图扩散解码LLM推理加速(326⭐)

AI交易相关爆发: polymarket-ai-trading×2, okx-agent-trade-kit, Pumpfun_AI_Trading_Bot, ai-auto-trading (共5个)

━━━ AI前沿一句话 ━━━
orthrus (326⭐) 提出双视图扩散解码实现无损LLM推理加速；elephant-agent (345⭐) 主打个人模型优先的自进化AI Agent；slopless (202⭐) 发布确定性textlint规则检测AI生成文本渣作。"""
push_feishu(msg, title="CS2 下午简报", msg_type="text")
