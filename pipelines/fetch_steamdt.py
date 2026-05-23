import requests, json, re, sys
from datetime import datetime, timezone, timedelta, time as dtime
import traceback

URL = 'https://www.steamdt.com/'
r = requests.get(URL, headers={'User-Agent': 'Chrome/120'}, timeout=15)

m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
data = json.loads(m.group(1))

def resolve(idx):
    if isinstance(idx, int):
        return data[idx]
    return idx

meta = resolve(1)
d = resolve(resolve(resolve(meta['data'])[1]))

# 大盘数据
for k, vref in d.items():
    v = resolve(vref)
    if isinstance(v, dict) and v.get('success'):
        dd = resolve(v['data'])
        if 'broadMarketIndex' in dd:
            bmi = resolve(dd['broadMarketIndex'])
            dy = resolve(dd['diffYesterday'])
            dyr = resolve(dd['diffYesterdayRatio'])
            print(f'大盘指数: {bmi}')
            print(f'日涨跌: {dy} ({dyr*100:.2f}%)')
            
            print()
            print('今日K线:')
            hlist = resolve(dd['historyMarketIndexList'])
            for h in hlist:
                h = resolve(h)
                ts = resolve(h[0])
                val = resolve(h[1])
                t = datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=8)))
                print(f'  {t.strftime("%H:%M")}: {val}')
            
            print()
            ts_ = resolve(dd['todayStatistics'])
            print(f'今日交易: {resolve(ts_[0])} 单, {resolve(ts_[1])} CNY')
            ys = resolve(dd['yesterdayStatistics'])
            print(f'昨日交易: {resolve(ys[0])} 单, {resolve(ys[1])} CNY')
            
            print()
            print(f'幸存数: {resolve(dd["surviveNum"])}')
            print(f'持有者数: {resolve(dd["holdersNum"])}')
            ut = resolve(dd['updateTime'])
            if isinstance(ut, (int, float)):
                if ut > 1e10:
                    ut = ut / 1000
                print(f'更新时间: {datetime.fromtimestamp(ut, tz=timezone(timedelta(hours=8)))}')
            break
