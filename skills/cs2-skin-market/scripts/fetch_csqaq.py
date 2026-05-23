#!/usr/bin/env python3
"""从 CSQAQ API 拉取大盘+品类数据。

依赖: 需在环境变量或参数中提供 CSQAQ_API_KEY

输出：JSON到stdout
"""

import urllib.request, json, os, sys

API_BASE = 'https://api.csqaq.com/api/v2'

def fetch_index(api_key):
    """拉取大盘指数"""
    req = urllib.request.Request(
        f'{API_BASE}/market/index',
        headers={'Authorization': f'Bearer {api_key}'}
    )
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read())

def fetch_trend(api_key, days='7d'):
    """拉取走势"""
    req = urllib.request.Request(
        f'{API_BASE}/market/trend?range={days}',
        headers={'Authorization': f'Bearer {api_key}'}
    )
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read())

def fetch_category_rank(api_key):
    """拉取品类涨跌排行"""
    req = urllib.request.Request(
        f'{API_BASE}/market/category/rank',
        headers={'Authorization': f'Bearer {api_key}'}
    )
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read())

def fetch_hot_items(api_key):
    """拉取热榜"""
    req = urllib.request.Request(
        f'{API_BASE}/market/hot',
        headers={'Authorization': f'Bearer {api_key}'}
    )
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read())

if __name__ == '__main__':
    api_key = os.environ.get('CSQAQ_API_KEY') or (sys.argv[1] if len(sys.argv) > 1 else None)
    if not api_key:
        print('需要CSQAQ_API_KEY环境变量或命令行参数', file=sys.stderr)
        sys.exit(1)
    
    result = {
        'index': fetch_index(api_key),
        'trend': fetch_trend(api_key),
        'category_rank': fetch_category_rank(api_key),
        'hot_items': fetch_hot_items(api_key)
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
