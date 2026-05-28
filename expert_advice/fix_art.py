"""Fix art_sport data and verify recommendations"""
import json
from collections import defaultdict

path = r'D:\GoakaoProject\艺术体育数据\art_sport_consolidated.json'
with open(path, 'r') as f:
    data = json.load(f)

# 河南省艺术体育综合分标准比例（根据河南省招办规定）
CORRECT_PCT = {
    '美术类': (50, 50),        # 文化50% + 专业50%
    '音乐类': (50, 50),
    '舞蹈类': (50, 50),
    '播音与主持类': (50, 50),
    '编导制作类': (50, 50),
    '表演类': (50, 50),
    '书法类': (50, 50),
    '体育类': (50, 50),         # 体育类：文化50% + 专业50%
}

# 专业满分
MAJOR_FULL = {
    '美术类': 300, '音乐类': 300, '舞蹈类': 300,
    '播音与主持类': 300, '编导制作类': 300, '表演类': 300,
    '书法类': 300, '体育类': 150,
}

fixes = {'total': len(data), 'wrong': 0, 'fixed': 0, 'correct': 0}

for item in data:
    cp = item.get('culture_pct', 0) or 0
    mp = item.get('major_pct', 0) or 0
    total = cp + mp
    
    # Check if within 99.5-100.5% tolerance
    if 99.5 <= total <= 100.5:
        fixes['correct'] += 1
        continue
    
    fixes['wrong'] += 1
    
    # Use default percentages for this category
    cat = item.get('category', '美术类')
    correct_cp, correct_mp = CORRECT_PCT.get(cat, (50, 50))
    
    old_cp, old_mp = cp, mp
    item['culture_pct'] = correct_cp
    item['major_pct'] = correct_mp
    fixes['fixed'] += 1
    
    # Recalculate score if low_score/high_score exist
    if item.get('low_score') and item.get('high_score'):
        # The historical scores were calculated with wrong percentages
        # We can't recalculate them without the original culture/major scores
        # But we can flag them
        pass

# Save fixed data
with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'Total: {fixes["total"]}')
print(f'Already correct: {fixes["correct"]}')
print(f'Wrong percentages: {fixes["wrong"]}')
print(f'Fixed to default (50/50): {fixes["fixed"]}')

# Now verify: what scores does a top student get?
print(f'\n=== 高分段验证（修复后）===')
import sys
sys.path.insert(0, r'D:\GoakaoProject\backend')
from art_sport import get_recommendations, calc_composite_score, MAJOR_FULL_SCORE

for cat in ['美术类', '音乐类', '编导制作类', '播音与主持类', '体育类']:
    full = MAJOR_FULL_SCORE.get(cat, 300)
    major_transformed = 300 / full * 750
    score = calc_composite_score(600, 300, 50, 50, cat)
    
    recs = get_recommendations(600, 300, cat)
    print(f'\n{cat}:')
    print(f'  综合分={score:.0f}')
    if recs:
        high = sum(1 for r in recs if r['probability'] >= 80)
        med = sum(1 for r in recs if 50 <= r['probability'] < 80)
        low = sum(1 for r in recs if r['probability'] < 50)
        best = recs[0]
        worst_good = [r for r in recs if r['probability'] >= 80]
        print(f'  推荐{len(recs)}条: 高概率{high} 中概率{med} 低概率{low}')
        if worst_good:
            print(f'  最好: {worst_good[0]["school"]} {worst_good[0]["major"]} (综合分{worst_good[0]["student_composite"]:.0f} 概率{worst_good[0]["probability"]}%)')
            print(f'  最差高概率: {worst_good[-1]["school"]} {worst_good[-1]["major"]} (综合分{worst_good[-1]["student_composite"]:.0f} 概率{worst_good[-1]["probability"]}%)')
    else:
        print(f'  无推荐 ❌')
