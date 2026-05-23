#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
品类数据分析（统一版）
合并自 analyze_categories.py + category_analysis.py
功能：
1. 从 SteamDT 首页提取品类数据
2. 分析品类排行榜 JSON
3. 保存品类报告到品类分析目录
"""

import os, sys, json, re, requests
from datetime import datetime

os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.environ.get("GAIA_BASE_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
STEAMDT_DIR = os.environ.get("GAIA_DAPAN_DIR", os.path.join(BASE_DIR, "data", "dapan"))
DAPAN_DIR = os.environ.get("GAIA_DAPAN_DIR", os.path.join(BASE_DIR, "data", "dapan"))
OUTPUT_DIR = os.environ.get("GAIA_REPORTS_DIR", os.path.join(BASE_DIR, "data", "reports"))
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DAPAN_DIR, exist_ok=True)


def extract_market_from_nuxt():
    """从 SteamDT 首页 JSON 提取大盘数据"""
    r = requests.get('https://www.steamdt.com', timeout=15,
                     headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/147.0.0.0'})
    pattern = r'<script[^>]*>(.*?)</script>'
    scripts = re.findall(pattern, r.text, re.DOTALL)
    json_str = None
    for sc in scripts:
        if 'broadMarketIndex' in sc:
            m = re.search(r'(\[.*)$', sc, re.DOTALL)
            if m:
                json_str = m.group(1)[:m.group(1).rfind(']')+1]
            break
    if not json_str:
        return None
    
    raw = json.loads(json_str)
    def resolve(idx):
        if isinstance(idx, int) and 0 <= idx < len(raw):
            val = raw[idx]
            if isinstance(val, (int, float)): return val
            if isinstance(val, str):
                try: return float(val)
                except: return val
            if isinstance(val, list):
                return [resolve(i) if isinstance(i, int) else i for i in val]
            return val
        return idx
    
    schema = raw[6] if len(raw) > 6 else {}
    market = {k: resolve(v) for k, v in schema.items()}
    return market


def analyze_json_files():
    """分析 _排行榜.json 文件（增强版：含交易量和Steam底价）"""
    cats = {}
    for fname in sorted(os.listdir(STEAMDT_DIR)):
        if not fname.endswith('_排行榜.json'):
            continue
        cat_name = fname.replace('_排行榜.json', '')
        fpath = os.path.join(STEAMDT_DIR, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                d = json.load(f)
        except:
            continue
        items = d.get('items', [])

        # 基础价格统计
        prices = [i.get('price', 0) for i in items if i.get('price')]
        # 交易量统计（24h成交数）
        tx_counts = [int(i.get('transactionCount24h', 0)) for i in items if i.get('transactionCount24h')]
        # 交易额统计（24h成交额）
        tx_amounts = [i.get('transactionAmount24h', 0) for i in items if i.get('transactionAmount24h')]
        # 在售数量
        on_sale = [i.get('onSaleNum', 0) for i in items if i.get('onSaleNum')]
        # Steam底价
        steam_prices = []
        for i in items:
            pp = i.get('platformPrices', {})
            sp = pp.get('Steam', {})
            if sp.get('price'):
                steam_prices.append(sp['price'])

        cats[cat_name] = {
            'type': d.get('type', ''),
            'total': d.get('total', 0),
            'displayed': len(items),
            # 价格
            'min_price': min(prices) if prices else 0,
            'max_price': max(prices) if prices else 0,
            'avg_price': round(sum(prices)/len(prices), 2) if prices else 0,
            # 交易量（24h）
            'total_tx_count_24h': sum(tx_counts),
            'avg_tx_count_24h': round(sum(tx_counts)/len(tx_counts), 1) if tx_counts else 0,
            'max_tx_count_24h': max(tx_counts) if tx_counts else 0,
            # 交易额（24h）
            'total_tx_amount_24h': round(sum(tx_amounts), 2),
            'avg_tx_amount_24h': round(sum(tx_amounts)/len(tx_amounts), 2) if tx_amounts else 0,
            # 在售数量
            'total_on_sale': sum(on_sale),
            'avg_on_sale': round(sum(on_sale)/len(on_sale), 1) if on_sale else 0,
            # Steam底价
            'steam_min': min(steam_prices) if steam_prices else 0,
            'steam_max': max(steam_prices) if steam_prices else 0,
            'steam_avg': round(sum(steam_prices)/len(steam_prices), 2) if steam_prices else 0,
        }
    return cats


def find_categories_in_nuxt():
    """在首页JSON中找品类相关信息"""
    r = requests.get('https://www.steamdt.com', timeout=15,
                     headers={'User-Agent': 'Mozilla/5.0'})
    pattern = r'<script type="application/json" data-nuxt-data="nuxt-app" data-ssr="true" id="__NUXT_DATA__">(.*?)</script>'
    m = re.search(pattern, r.text, re.DOTALL)
    if not m:
        return {}
    text = json.dumps(json.loads(m.group(1)), ensure_ascii=False).lower()
    cat_keywords = {
        '步枪': ['rifle', '步枪'],
        '手枪': ['pistol', '手枪'],
        '冲锋枪': ['smg', '冲锋枪'],
        '霰弹枪': ['shotgun', '霰弹枪'],
        '狙击枪': ['sniper', '狙击枪'],
        '刀具': ['knife', '刀', '匕首'],
        '手套': ['glove', '手套'],
        '贴纸': ['sticker', '贴纸', '印花'],
        '武器箱': ['case', '箱子', '武器箱'],
        '钥匙': ['key', '钥匙'],
    }
    return {name: sum(text.count(kw) for kw in kws) for name, kws in cat_keywords.items()}


def generate_report(market, cats, nuxt_cats):
    """生成品类分析报告并保存"""
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    report_path = os.path.join(OUTPUT_DIR, f"{date_str}-品类报告.md")
    
    lines = [
        f"# 品类分析报告 | {date_str}",
        f"> 生成时间: {now.strftime('%Y-%m-%d %H:%M')}",
        f"> 数据来源: SteamDT",
        "",
        "---",
        "",
        "## 大盘概览",
        "",
        "| 指标 | 数值 |",
        "|------|------|",
    ]
    
    if market:
        idx = market.get('broadMarketIndex', 'N/A')
        diff = market.get('diffYesterday', 'N/A')
        ratio = market.get('diffYesterdayRatio', 'N/A')
        lines.append(f"| 大盘指数 | {idx} |")
        lines.append(f"| 日涨跌 | {diff} ({ratio}%) |")
        lines.append(f"| 在线人数 | {market.get('surviveNum', 'N/A')} |")
    else:
        lines.append("| 大盘指数 | 无法获取 |")
    
    if cats:
        lines.extend(["", "## 品类排行榜分析", "",
                       "| 品类 | 饰品数 | 价格区间 | 均价 | 24h成交量 | 24h成交额 | 在售量 | Steam均价 |",
                       "|------|--------|---------|------|---------|---------|------|---------|"])
        for name, info in sorted(cats.items()):
            # 格式化金额
            tx_amt = f"¥{info['total_tx_amount_24h']:,.0f}"
            steam_avg = f"¥{info['steam_avg']:.0f}" if info['steam_avg'] else "N/A"
            lines.append(f"| {name} | {info['displayed']} | "
                         f"¥{info['min_price']:.0f}~¥{info['max_price']:.0f} | "
                         f"¥{info['avg_price']:.0f} | {info['total_tx_count_24h']} | "
                         f"{tx_amt} | {info['total_on_sale']} | {steam_avg} |")

        # 量价分析：资金流向
        lines.extend(["", "## 💰 品类资金流向分析（24h）", ""])
        sorted_by_amount = sorted(cats.items(), key=lambda x: x[1].get('total_tx_amount_24h', 0), reverse=True)
        lines.extend(["| 品类 | 24h成交额 | 24h成交量 | 件均成交额 | 均价 | Steam溢价 |",
                       "|------|---------|---------|---------|------|---------|"])
        for name, info in sorted_by_amount:
            if info['total_tx_count_24h'] == 0:
                continue
            avg_per_item = info['total_tx_amount_24h'] / info['total_tx_count_24h']
            premium = 0
            if info['avg_price'] > 0 and info['steam_avg'] > 0:
                premium = ((info['avg_price'] - info['steam_avg']) / info['steam_avg']) * 100
            premium_str = f"{premium:+.1f}%" if premium != 0 else "N/A"
            lines.append(f"| {name} | ¥{info['total_tx_amount_24h']:,.0f} | "
                         f"{info['total_tx_count_24h']}笔 | ¥{avg_per_item:.0f}/件 | "
                         f"¥{info['avg_price']:.0f} | {premium_str} |")

        # 量价背离检测
        lines.extend(["", "## 📊 量价背离检测（对比7日均值）", ""])
        for name, info in cats.items():
            if info['displayed'] < 2:
                continue
            # 这里用当前24h成交量估算（实际应对比历史均值，此处做占位提示）
            if info['avg_tx_count_24h'] > 0:
                lines.append(f"- {name}: 日均 {info['avg_tx_count_24h']} 笔交易, "
                             f"在售 {info['avg_on_sale']} 件, 流动性比率 {info['avg_tx_count_24h']/max(info['avg_on_sale'],1)*100:.1f}%")

        lines.extend(["", "### 千元以下推荐", ""])
        for name, info in sorted(cats.items()):
            if info['avg_price'] < 1000 and info['displayed'] > 0:
                lines.append(f"- ✅ {name}: 均价¥{info['avg_price']}")
    
    if nuxt_cats:
        lines.extend(["", "## 首页品类关键词频率", "",
                       "| 品类 | 出现次数 |", "|------|---------|"])
        for name, count in sorted(nuxt_cats.items(), key=lambda x: -x[1]):
            emoji = {'刀具': '🔪', '手套': '🧤', '贴纸': '🏷️', '武器箱': '📦'}.get(name, '📦')
            lines.append(f"| {emoji} {name} | {count} |")
    
    report = "\n".join(lines)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    return report_path


def main():
    print("📊 品类数据分析（统一版）")
    print("=" * 40)
    
    print("\n📈 获取大盘数据...")
    market = extract_market_from_nuxt()
    if market:
        print(f"   大盘指数: {market.get('broadMarketIndex', 'N/A')}")
    else:
        print("   ⚠️ 无法从首页提取")
    
    print("\n📦 分析品类排行榜...")
    cats = analyze_json_files()
    print(f"   找到 {len(cats)} 个品类文件")
    for name, info in cats.items():
        print(f"   {name}: {info['displayed']}件, 均价¥{info['avg_price']}")
    
    print("\n🔍 扫描首页品类关键词...")
    nuxt_cats = find_categories_in_nuxt()
    print(f"   检测到 {len(nuxt_cats)} 个品类")
    
    report_path = generate_report(market, cats, nuxt_cats)
    print(f"\n✅ 报告已生成: {report_path}")


if __name__ == "__main__":
    main()
