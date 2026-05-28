"""Analyze art_sport data issues"""
import json, os
from collections import Counter

path = r'D:\GoakaoProject\艺术体育数据\art_sport_consolidated.json'
with open(path, 'r') as f:
    data = json.load(f)

print(f'总记录: {len(data)}')

# 1. Check culture_pct + major_pct sums
sum_issues = []
for item in data:
    a = item.get('culture_pct', 0) or 0
    b = item.get('major_pct', 0) or 0
    if abs(a + b - 100) > 0.5:  # not adding up to ~100
        sum_issues.append(item)

print(f'\n=== culture_pct+major_pct 不等于100%的记录: {len(sum_issues)} ===')
# Show distribution of sums
sum_dist = Counter()
for item in sum_issues:
    s = round((item.get('culture_pct',0) or 0) + (item.get('major_pct',0) or 0), 1)
    sum_dist[s] += 1

for s, c in sorted(sum_dist.items()):
    print(f'  总和={s}%: {c}条')

# Show a few examples
print(f'\n前5条异常记录:')
for item in sum_issues[:5]:
    print(f'  {item["school"]:25s} {item["major"]:25s} {item["category"]:8s} '
          f'文化占比={item["culture_pct"]:5.1f}% 专业占比={item["major_pct"]:5.1f}% '
          f'合计={item["culture_pct"]+item["major_pct"]:.0f}%')

# 2. Check score ranges
print(f'\n=== 各类别综合分范围 ===')
from collections import defaultdict
cat_scores = defaultdict(list)
for item in data:
    cat = item['category']
    lo = item.get('low_score')
    hi = item.get('high_score')
    if lo and hi:
        cat_scores[cat].append((lo, hi))

for cat in sorted(cat_scores.keys()):
    los = [s[0] for s in cat_scores[cat]]
    his = [s[1] for s in cat_scores[cat]]
    print(f'  {cat:10s} low: {min(los):.0f}~{max(los):.0f}  high: {min(his):.0f}~{max(his):.0f}  ({len(cat_scores[cat])}条)')

# 3. Check: if a student has 600 culture, 300 major, where would they rank?
from art_sport import get_recommendations, calc_composite_score

print(f'\n=== 高分段学生测试 (文化600 专业300, 文理各半===')
# Try each category
from art_sport import MAJOR_FULL_SCORE, DEFAULT_PCT
for cat, full in sorted(MAJOR_FULL_SCORE.items()):
    major_transformed = 300 / full * 750
    cp, mp = DEFAULT_PCT.get(cat, (50, 50))
    score = 600 * cp / 100 + major_transformed * mp / 100
    print(f'  {cat:10s} 专业满分={full} 综合分={score:.0f} (文化{cp}%+专业{mp}%)')

# Now get recommendations
for cat in ['美术类', '音乐类', '编导制作类', '体育类']:
    recs = get_recommendations(600, 300, cat)
    if recs:
        best = recs[0]
        print(f'\n{cat}: 文化600专业300 -> 推荐{len(recs)}条, 最好: {best["school"]} {best["major"]} 综合分={best["student_composite"]:.0f} 概率={best["probability"]}%')
        # Count by probability
        high = sum(1 for r in recs if r['probability'] >= 80)
        medium = sum(1 for r in recs if 50 <= r['probability'] < 80)
        low = sum(1 for r in recs if r['probability'] < 50)
        print(f'    高概率({">=80"}): {high} 中概率(50-80): {medium} 低概率(<50): {low}')
    else:
        print(f'\n{cat}: 无推荐')
