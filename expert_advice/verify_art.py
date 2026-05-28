"""Verify art recommendations work correctly now"""
import sys
sys.path.insert(0, r'D:\GoakaoProject\backend')
from art_sport import get_recommendations

# Top student: culture 600, major 300
print('=== 艺术类高分段测试 (文化600 专业300) ===')
for cat in ['美术类', '音乐类', '编导制作类', '播音与主持类', '表演类', '体育类']:
    recs = get_recommendations(600, 300, cat)
    if not recs:
        print(f'\n{cat}: 无数据')
        continue
    
    high80 = [r for r in recs if r['probability'] >= 80]
    mid = [r for r in recs if 50 <= r['probability'] < 80]
    low = [r for r in recs if r['probability'] < 50]
    
    print(f'\n{cat} ({len(recs)}条): 高概率>=80%: {len(high80)}  中: {len(mid)}  低: {len(low)}')
    
    # Show top 5
    print(f'  前5推荐:')
    for r in recs[:5]:
        print(f'    {r["school"]:25s} {r["major"]:25s} 综合分={r["student_composite"]:.0f} 历史{r["min_score"]:.0f}~{r["max_score"]:.0f} 概率{r["probability"]}%')
    
    # Show high-probability bottom 3
    if len(high80) > 5:
        print(f'  高概率区最差的几个:')
        for r in high80[-3:]:
            print(f'    {r["school"]:25s} {r["major"]:25s} 综合分={r["student_composite"]:.0f} 历史{r["min_score"]:.0f}~{r["max_score"]:.0f} 概率{r["probability"]}%')

# Also test a mid-range student
print('\n\n=== 中等分段测试 (文化450 专业240) ===')
for cat in ['美术类', '音乐类', '编导制作类', '播音与主持类', '表演类', '体育类']:
    recs = get_recommendations(450, 240, cat)
    if not recs:
        continue
    high80 = sum(1 for r in recs if r['probability'] >= 80)
    print(f'{cat}: 推荐{len(recs)}条, >=80%: {high80}条')
    if recs:
        print(f'  最好: {recs[0]["school"]:25s} {recs[0]["major"]:25s} 综合分={recs[0]["student_composite"]:.0f} 概率{recs[0]["probability"]}%')
