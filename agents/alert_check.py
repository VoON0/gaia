#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SteamDT 行情预警检查脚本
每小时跑一次，检查配置的预警条件是否触发
触发则推送飞书
"""

import requests
import json
import os
import sys
from datetime import datetime

# --- 配置 ---
ALERTS_CONFIG = r"D:\Knowledge\config\alerts.json"
STATE_FILE = r"D:\Knowledge\data\alert_state.json"
DAPAN_SAVE_DIR = r"D:\Knowledge\大盘数据"

# 飞书配置
FEISHU_APP_ID = "cli_a97408dad2389bee"
FEISHU_APP_SECRET = "2TFaYEA1VTHAFblIMTNudfSPP0gZPLiS"
FEISHU_CHAT_ID = "oc_6c931269c43e3f8c1a0ba4a98a5ab958"

def ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def get_feishu_token():
    """获取飞书tenant access token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }, timeout=10)
    return resp.json().get("tenant_access_token", "")

def push_feishu(content):
    """推送到飞书"""
    token = get_feishu_token()
    if not token:
        print("  ❌ 获取飞书token失败")
        return False
    
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    resp = requests.post(url, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }, json={
        "receive_id": FEISHU_CHAT_ID,
        "msg_type": "text",
        "content": json.dumps({"text": content})
    }, timeout=10)
    
    return resp.json().get("code") == 0

def fetch_summary():
    """获取大盘统计数据，返回dict"""
    r = requests.get('https://www.steamdt.com/api/index/statistics/v1/summary', timeout=15)
    return r.json().get('data', {})

def fetch_players():
    """获取日K数据（在线人数）"""
    r = requests.get('https://www.steamdt.com/api/index/players/v1/statistics', timeout=15)
    return r.json().get('data', {})

def load_state():
    """加载上次的检查状态"""
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"last_alerted": {}, "history": {}}

def save_state(state):
    """保存检查状态"""
    ensure_dir(STATE_FILE)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def check_page_source_for_categories():
    """备用方案：尝试从首页JSON找品类数据"""
    url = 'https://www.steamdt.com'
    try:
        r = requests.get(url, timeout=15)
        text = r.text
        import re
        pattern = '<script type="application/json" data-nuxt-data="nuxt-app" data-ssr="true" id="__NUXT_DATA__">(.*?)</script>'
        m = re.search(pattern, text, re.DOTALL)
        if m:
            return json.loads(m.group(1))
    except:
        pass
    return None

def main():
    now = datetime.now()
    time_str = now.strftime("%Y-%m-%d %H:%M")
    date_str = now.strftime("%Y-%m-%d")
    hour = now.hour
    
    print(f"🔍 [{time_str}] SteamDT 行情预警检查开始")
    
    # 1. 加载配置
    try:
        with open(ALERTS_CONFIG, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"  ❌ 读取配置失败: {e}")
        return
    
    # 2. 获取数据
    stats = fetch_summary()
    players_data = fetch_players()
    
    # 3. 计算指标
    broad_index = stats.get('broadMarketIndex', 0)
    diff_yest = stats.get('diffYesterday', 0)
    diff_ratio = stats.get('diffYesterdayRatio', 0)
    sentiment = stats.get('transPerformanceTrend', {}).get('performanceScore', 50)
    sentiment_diff = stats.get('transPerformanceTrend', {}).get('diffYesterdayScore', 0)
    rise_fall_type = stats.get('riseFallType', 'UP')
    rise_fall_days = stats.get('riseFallDays', 0)
    today_stats = stats.get('todayStatistics', {})
    history_list = players_data.get('historyList', [])
    
    # 在线人数分析
    online_30d = [(int(x[1]), int(x[2])) for x in history_list[-30:]] if history_list else []
    current_online = online_30d[-1][0] if online_30d else 0
    online_7d_avg = sum(x[0] for x in online_30d[-7:]) / max(len(online_30d[-7:]), 1) if online_30d else 0
    
    # 新增饰品量分析
    add_num_today = int(today_stats.get('addNum', 0))
    daily_add_nums = []
    for item in history_list[-7:]:
        # 从日K里我们只拿到在线人数和交易笔数，没有新增饰品量
        # 新增饰品量需要每天存
        pass
    
    # 连跌天数
    consecutive_down = rise_fall_days if rise_fall_type == 'DOWN' else 0
    consecutive_up = rise_fall_days if rise_fall_type == 'UP' else 0
    
    # 4. 检查预警条件
    triggered = []
    state = load_state()
    last_alerted = state.get('last_alerted', {})
    
    checks = [
        ("大盘", "日跌幅超过3%", diff_ratio < -3),
        ("大盘", "情绪跌破30", sentiment < 30),
        ("大盘", "连跌5天以上", consecutive_down >= 5),
        ("大盘", "日涨幅超过5%（暴涨）", diff_ratio > 5),
        ("玩家", "在线人数跌破历史低位", online_30d and current_online == min(x[0] for x in online_30d)),
        ("玩家", "在线人数创新高", online_30d and current_online == max(x[0] for x in online_30d)),
    ]
    
    for group, rule_name, condition in checks:
        if not condition:
            continue
        
        # 检查是否已经推送过（防止重复推送）
        alert_key = f"{group}:{rule_name}"
        last_time = last_alerted.get(alert_key, "")
        
        # 如果是第一次触发，或者上次触发超过6小时了，就再推
        skip = False
        if last_time:
            try:
                last_dt = datetime.strptime(last_time, "%Y-%m-%d %H")
                hours_since = (now - last_dt).total_seconds() / 3600
                if hours_since < 6:
                    skip = True
            except:
                pass
        
        if skip:
            print(f"  ⏭ {rule_name}: 已触发过（{last_time}），6小时内不重复推送")
            continue
        
        triggered.append((group, rule_name))
    
    # 5. 如果有触发，推送飞书
    if triggered:
        msg = f"🚨 SteamDT 行情预警\n━━━━━━━━━━━━━━\n"
        msg += f"时间: {time_str}\n"
        msg += f"大盘: {broad_index} ({diff_yest:+.2f}, {diff_ratio:+.2f}%)\n"
        msg += f"情绪: {sentiment} ({sentiment_diff:+d})\n\n"
        msg += "触发预警:\n"
        for group, rule_name in triggered:
            msg += f"  ⚠️ [{group}] {rule_name}\n"
            # 记录推送时间
            last_alerted[f"{group}:{rule_name}"] = time_str[:13]  # YYYY-MM-DD HH
        
        msg += f"\n🕐 检查时间: {time_str}"
        
        print(f"\n  🚨 触发 {len(triggered)} 条预警!")
        for g, r in triggered:
            print(f"     [{g}] {r}")
        print(f"  📤 推送飞书...")
        
        ok = push_feishu(msg)
        if ok:
            print(f"  ✅ 飞书推送成功!")
        else:
            print(f"  ❌ 飞书推送失败!")
        
        # 更新状态
        state['last_alerted'] = last_alerted
        save_state(state)
    else:
        # 没触发也更新一下 "我活着的" 状态
        state['last_check'] = time_str
        state['last_index'] = broad_index
        save_state(state)
        print(f"\n  ✅ 无预警触发，一切正常")
    
    print(f"\n  大盘指数: {broad_index} | 涨跌: {diff_yest:+.2f} ({diff_ratio:+.2f}%) | 情绪: {sentiment}")

if __name__ == "__main__":
    main()
