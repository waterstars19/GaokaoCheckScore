"""Check 郑州大学 临床医学 duplicates in cleaned data"""
import json
from collections import Counter

with open(r'D:\GoakaoProject\docs\admission_plans.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)
d = raw['data']

# 过滤郑州大学临床医学
zzu_clinic = [item for item in d if '郑州大学' in (item.get('school','') or '') and '临床医学' in (item.get('major','') or '')]
print(f"郑州大学 临床医学 总条数: {len(zzu_clinic)}")

# 按 year + major + category 分组
groups = Counter()
for item in zzu_clinic:
    key = (item.get('year',''), item.get('major',''), item.get('category',''))
    groups[key] += 1

print(f"不同组合数: {len(groups)}")
print("\n前20条按 year+major+category 分组:")
for k, c in sorted(groups.items(), key=lambda x: (x[0][0], x[0][1]))[:20]:
    print(f"  {k[0]} | {k[1][:40]:40s} | {k[2]:6s} | {c}条")

# 同一个 school+year+major 内有重复吗？
from collections import defaultdict
dup_check = defaultdict(list)
for item in zzu_clinic:
    key = (item.get('school',''), item.get('year',''), item.get('major',''), item.get('category',''))
    dup_check[key].append(item)

multi = {k: v for k, v in dup_check.items() if len(v) > 1}
print(f"\n同一个 school+year+major+category 有重复的: {len(multi)} 组")
for k, v in list(multi.items())[:5]:
    print(f"  {k}: {len(v)}条")
    for item in v[:3]:
        print(f"    planned_count={item.get('planned_count')} tuition={item.get('tuition')} direction={item.get('direction','')}")
