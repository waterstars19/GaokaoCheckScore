"""Print batch5 summary"""
import json

with open(r'D:\GoakaoProject\expert_advice\batch5\expert_summary.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

print(f'Total videos: {d["total"]}')
total_opinions = 0
total_keywords = 0
for v in d['videos']:
    t = v.get('video_title', v.get('file', '?'))
    ops = len(v.get('expert_opinions', []))
    kws = len(v.get('keywords', []))
    topics = v.get('topics', [])
    total_opinions += ops
    total_keywords += kws
    print(f'  {t}')
    print(f'    -> {ops} opinions, {kws} keywords, topics: {topics}')

print(f'\nTotal: {total_opinions} expert opinions, {total_keywords} keywords')
