#!/usr/bin/env python3
"""从 SteamDT 提取大盘数据。

两种方式自动切换：
1. __NUXT_DATA__ JSON数组解析（优先）
2. HTML正则提取（后备）

输出：JSON到stdout
"""

import re, json, sys, urllib.request

URL = 'https://www.steamdt.com/'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}


def fetch():
    req = urllib.request.Request(URL, headers=HEADERS)
    resp = urllib.request.urlopen(req, timeout=15)
    return resp.read().decode('utf-8', errors='replace')


def extract_html(html):
    """从 HTML 文本中正则提取关键数据（比Nuxt更健壮）"""
    result = {}

    # 大盘指数
    m = re.search(r'counter-container[^>]*>(\d+\.\d+)', html)
    if m:
        result['index'] = float(m.group(1))

    # 日涨跌值和百分比
    m = re.search(r'\-?\d+\.\d+</span>\s*<span[^>]*text-14[^>]*>[+]?(-?\d+\.\d+)%', html)
    if m:
        result['diff_ratio'] = float(m.group(1))

    # 连涨/连跌天数
    m = re.search(r'连(涨|跌)\s*(\d+)天', html)
    if m:
        result['streak'] = {'direction': m.group(1), 'days': int(m.group(2))}

    # 昨日成交额环比
    m = re.search(r'环比:\s*<span[^>]*>([↓↑])\s*(-?\d+\.?\d*)%', html)
    if m:
        direction = -1 if m.group(1) == '↓' else 1
        result['amount_change_pct'] = direction * float(m.group(2))

    result['source'] = 'html'
    return result


def extract_daily_data(html):
    """从NuxT中提取每日成交数据（日期, 成交量, 成交额）"""
    dates = re.findall(r'"(\d{4}-\d{2}-\d{2})","(\d+)","(\d+)"', html)
    return [{'date': d, 'volume': int(v), 'amount': int(a)} for d, v, a in dates]


if __name__ == '__main__':
    html = fetch()
    
    result = extract_html(html)
    if result.get('index'):
        result['daily'] = extract_daily_data(html)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({'error': '无法提取数据', 'html_snippet': html[:500]}, ensure_ascii=False))
        sys.exit(1)
