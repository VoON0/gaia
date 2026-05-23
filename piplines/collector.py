#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一数据采集器（整合版）
合并自 crawl_dapan.py + crawl_github.py + crawl_ai_experts.py
用法:
  python collector.py --all         # 全量采集
  python collector.py --dapan       # 仅大盘
  python collector.py --github      # 仅热榜
  python collector.py --experts     # 仅AI大神
"""

import os, sys, json, re, glob, subprocess
from datetime import datetime

os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

OUTPUT_DIR = r"D:\Knowledge"
DAPAN_DIR = os.path.join(OUTPUT_DIR, "大盘数据")
EXPERT_DIR = os.path.join(OUTPUT_DIR, "大神观点")
GITHUB_DIR = os.path.join(OUTPUT_DIR, "GitHub热榜")
os.makedirs(DAPAN_DIR, exist_ok=True)
os.makedirs(EXPERT_DIR, exist_ok=True)
os.makedirs(GITHUB_DIR, exist_ok=True)


# ===================== 大盘数据 =====================

def resolve_nuxt_index(raw, idx):
    """通过索引从 Nuxt payload 取原始值，不递归"""
    if isinstance(idx, int) and 0 <= idx < len(raw):
        val = raw[idx]
        if isinstance(val, (int, float)):
            return val
        if isinstance(val, str):
            try: return round(float(val.replace(',', '')), 2)
            except: return val
        return val
    return idx

def resolve_nuxt_dict(raw, schema_dict):
    """把 Nuxt schema 字典解析成实际数据字典"""
    result = {}
    for k, v in schema_dict.items():
        val = resolve_nuxt_index(raw, v)
        if isinstance(val, dict):
            # 嵌套 schema
            val = resolve_nuxt_dict(raw, val)
        result[k] = val
    return result


def collect_dapan():
    """采集 SteamDT 大盘数据（完整 Nuxt payload -> 全字段）"""
    import urllib.request, ssl
    ctx = ssl._create_unverified_context()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/147.0.0.0'}
    req = urllib.request.Request('https://www.steamdt.com/', headers=headers)
    r = urllib.request.urlopen(req, timeout=15, context=ctx)
    html = r.read().decode('utf-8', errors='replace')

    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    target = None
    for sc in scripts:
        if 'broadMarketIndex' in sc:
            target = sc
            break
    if not target:
        return "❌ 未找到大盘数据"

    m = re.search(r'(\[.*)$', target, re.DOTALL)
    if not m:
        return "❌ JSON 匹配失败"
    json_str = m.group(1)[:m.group(1).rfind(']')+1]
    raw = json.loads(json_str)

    # schema 在第6个元素: { broadMarketIndex: 7, diffYesterday: 8, todayStatistics: 85, ... }
    schema = raw[6]
    market = resolve_nuxt_dict(raw, schema)

    idx = market.get('broadMarketIndex', '?')
    diff = market.get('diffYesterday', '?')
    ratio = market.get('diffYesterdayRatio', '?')
    survive = market.get('surviveNum', '?')  # 存世量(件)
    holders = market.get('holdersNum', '?')  # 持有者(人)
    update_time = market.get('updateTime', '?')

    # 今日统计
    ts = market.get('todayStatistics', {})
    if not isinstance(ts, dict): ts = {}
    today_trade = ts.get('tradeNum', '?')
    today_trade_volume = ts.get('tradeVolumeRatio', '?')
    today_trade_amount = ts.get('tradeAmountRatio', '?')
    today_add = ts.get('addNum', '?')
    today_add_val = ts.get('addValuation', '?')
    today_add_ratio = ts.get('addNumRatio', '?')
    today_turnover = ts.get('turnover', '?')

    # 昨日统计
    ys = market.get('yesterdayStatistics', {})
    if not isinstance(ys, dict): ys = {}
    yes_trade = ys.get('tradeNum', '?')
    yes_add = ys.get('addNum', '?')
    yes_turnover = ys.get('turnover', '?')

    # 涨跌统计
    rise_fall_type = market.get('riseFallType', '?')
    rise_fall_days = market.get('riseFallDays', '?')

    # 走势分值
    perf = market.get('transPerformanceTrend', {})
    if not isinstance(perf, dict): perf = {}
    perf_score = perf.get('performanceScore', '?')
    perf_diff = perf.get('diffYesterdayScore', '?')

    date = datetime.now().strftime('%Y-%m-%d')
    # 格式化数字
    def fmt(v):
        if v == '?' or v is None: return 'N/A'
        try:
            f = float(v)
            if f >= 10000: return f'{f/10000:.2f}万'
            if f >= 1000: return f'{f/10000:.2f}万'
            return str(f)
        except:
            return str(v)

    def fmt_money(v):
        if v == '?' or v is None: return 'N/A'
        try:
            f = float(v)
            if f >= 100000000: return f'{f/100000000:.2f}亿'
            if f >= 10000: return f'{f/10000:.2f}万'
            return str(f)
        except:
            return str(v)

    path = os.path.join(DAPAN_DIR, f"{date}-大盘数据.md")
    header = f"""---
date: {date}
tags: [CS2, 大盘数据, SteamDT]
source: SteamDT
---

# CS2 大盘数据 | {date}

> 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 大盘概览

| 指标 | 数值 |
|------|------|
| 大盘指数 | **{idx}** |
| 日涨跌 | {diff} ({ratio}%) |
| 存世量 | {fmt(survive)} 件 |
| 持有者 | {fmt(holders)} 人 |

## 今日交易统计

| 指标 | 今日 |
|------|------|
| 交易笔数 | {fmt(today_trade)} |
| 成交额 | {fmt_money(today_turnover)} |
| 新增饰品 | {fmt(today_add)} |
| 新增估值 | {fmt_money(today_add_val)} |
| 笔数同比 | {today_trade_volume}% |
| 金额同比 | {today_trade_amount}% |

## 涨跌趋势

| 指标 | 数值 |
|------|------|
| 涨跌类型 | {rise_fall_type} |
| 连涨/跌天数 | {rise_fall_days} |
| 走势评分 | {perf_score} |
| 评分日变化 | {perf_diff} |
"""
    json_data = {
        'index': idx, 'diff': diff, 'ratio': f'{ratio}%',
        'online': survive, 'holders': holders,
        'trade_num': today_trade, 'turnover': today_turnover,
        'add_num': today_add, 'add_valuation': today_add_val,
        'yesterday_trade': yes_trade, 'yesterday_add': yes_add,
        'yesterday_turnover': yes_turnover, 'update_time': str(update_time),
    }
    json_block = json.dumps(json_data, ensure_ascii=False, indent=2)
    footer = f'\n## 原始数据\n\n```json\n{json_block}\n```\n'
    content = header + footer
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return f"大盘: idx={idx} | diff={diff}({ratio}%) | 存世={survive} | 交易={today_trade} | 额={today_turnover}"


# ===================== GitHub 热榜 =====================

def collect_github():
    """采集 GitHub Trending（合并自 crawl_github.py）"""
    import requests as rq
    repos = []
    
    # 尝试 GitHub API
    try:
        url = "https://api.github.com/search/repositories"
        params = {"q": "topic:ai created:>2026-01-01 stars:>50",
                   "sort": "stars", "order": "desc", "per_page": 15}
        headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "GitHub-Crawler"}
        r = rq.get(url, params=params, headers=headers, timeout=30, verify=False)
        if r.status_code == 200:
            repos = r.json().get("items", [])
    except:
        pass
    
    # API 失败则扫 Trending 页面
    if not repos:
        try:
            r = rq.get('https://github.com/trending', timeout=30,
                       headers={'User-Agent': 'Mozilla/5.0'})
            matches = re.findall(r'<h2[^>]*>.*?<a[^>]*href="/([^"]+)"[^>]*>\s*([^\s<]+)', r.text, re.DOTALL)
            for path, name in matches[:15]:
                repos.append({"full_name": path, "name": name,
                              "html_url": f"https://github.com/{path}",
                              "stargazers_count": 0, "language": "", "description": ""})
        except:
            pass
    
    date = datetime.now().strftime('%Y-%m-%d')
    path = os.path.join(GITHUB_DIR, f"{date}-热榜.md")
    
    lines = [f"# GitHub AI 热榜 | {date}",
             f"> 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             "", "## 🔥 Top 项目", "",
             "| # | 项目 | Stars | 语言 | 简介 |",
             "|---|------|-------|------|------|"]
    for i, repo in enumerate(repos[:15], 1):
        name = repo.get('full_name', repo.get('name', '?'))
        stars = repo.get('stargazers_count', 0)
        lang = repo.get('language') or '—'
        desc = (repo.get('description') or '')[:60]
        url = repo.get('html_url', f"https://github.com/{name}")
        lines.append(f"| {i} | [{name}]({url}) | ★{stars} | {lang} | {desc} |")
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return f"✅ GitHub: {len(repos)} 个项目"


# ===================== AI 大神观点 =====================

def collect_experts():
    """采集 AI 前沿信息（合并自 crawl_ai_experts.py）"""
    import requests as rq
    date = datetime.now().strftime('%Y-%m-%d')
    
    # arXiv 论文
    papers = []
    try:
        r = rq.get("https://export.arxiv.org/api/query", params={
            "search_query": "cat:cs.AI", "sortBy": "submittedDate",
            "sortOrder": "descending", "max_results": 6
        }, timeout=15, verify=False)
        entries = re.findall(r'<entry>(.*?)</entry>', r.text, re.DOTALL)
        for entry in entries[:6]:
            t = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
            l = re.search(r'<id>(.*?)</id>', entry)
            s = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
            if t:
                papers.append((t.group(1).strip()[:80], l.group(1).strip() if l else '',
                               s.group(1).strip()[:150] if s else ''))
    except:
        pass
    
    # Hacker News
    hn = []
    try:
        r = rq.get("https://hn.algolia.com/api/v1/search", params={
            "query": "AI", "tags": "story", "hitsPerPage": 6
        }, timeout=15, verify=False)
        for hit in r.json().get("hits", [])[:6]:
            hn.append({"title": hit.get("title", ""),
                       "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                       "points": hit.get("points", 0)})
    except:
        pass
    
    path = os.path.join(EXPERT_DIR, f"{date}-大神观点.md")
    lines = [f"# AI 前沿动态 | {date}",
             f"> 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             "", "## arXiv 最新 AI 论文", ""]
    for i, (t, l, s) in enumerate(papers, 1):
        lines.append(f"{i}. [{t}]({l}) — {s}")
    
    lines.extend(["", "## Hacker News AI 热门", ""])
    for i, item in enumerate(hn, 1):
        lines.append(f"{i}. [{item['title']}]({item['url']}) ★{item['points']}")
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return f"✅ 动态: 论文{len(papers)}篇, HN{len(hn)}条"


# ===================== CLI =====================

def print_help():
    print("用法: python collector.py [选项]")
    print("  --all       全量采集（默认）")
    print("  --dapan     仅大盘数据")
    print("  --github    仅 GitHub 热榜")
    print("  --experts   仅 AI 动态")

if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print_help()
        sys.exit(0)
    
    if "--all" in sys.argv or len(sys.argv) == 1:
        print("📦 全量采集开始...")
        print(collect_dapan())
        print(collect_github())
        print(collect_experts())
        print("✅ 全量采集完成")
    elif "--dapan" in sys.argv:
        # 调用独立的 crawl_dapan.py
        import subprocess, sys as _sys
        result = subprocess.run(
            [_sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "crawl_dapan.py")],
            capture_output=True, text=True
        )
        print(result.stdout.strip())
        if result.returncode != 0:
            print(result.stderr.strip()[:500])
    elif "--github" in sys.argv:
        print(collect_github())
    elif "--experts" in sys.argv:
        print(collect_experts())
    else:
        print_help()
