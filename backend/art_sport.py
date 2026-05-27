"""
艺术体育类志愿推荐模块
"""
import json, os, math

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(PROJECT_DIR, '艺术体育数据', 'art_sport_consolidated.json')

# 艺术类/体育类专业满分
MAJOR_FULL_SCORE = {
    '美术类': 300, '音乐类': 300, '舞蹈类': 300,
    '播音与主持类': 300, '编导制作类': 300, '表演类': 300,
    '书法类': 300, '体育类': 150,
}

# 艺术类别列表（前端展示用）
ART_CATEGORIES = ['美术类', '音乐类', '舞蹈类', '播音与主持类', '编导制作类', '表演类', '书法类', '体育类']

# 类别名称映射（简写→全称）
CAT_ALIAS = {
    '美术': '美术类', '美术与设计': '美术类',
    '音乐': '音乐类',
    '舞蹈': '舞蹈类', '国标': '舞蹈类',
    '播音': '播音与主持类', '主持': '播音与主持类',
    '编导': '编导制作类',
    '表演': '表演类',
    '书法': '书法类',
    '体育': '体育类',
}

# 综合分默认公式（当 culture_pct/major_pct 缺失时使用）
DEFAULT_PCT = {
    '美术类': (50, 50),
    '音乐类': (50, 50),
    '舞蹈类': (50, 50),
    '播音与主持类': (50, 50),
    '编导制作类': (50, 50),
    '表演类': (50, 50),
    '书法类': (50, 50),
    '体育类': (50, 50),
}


def load_data():
    """加载艺术体育数据"""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def calc_composite_score(culture, major, culture_pct, major_pct, category):
    """
    计算综合分
    艺术类公式: 综合分 = 文化×culture_pct% + (专业/300×750)×major_pct%
    体育类公式: 综合分 = 文化×culture_pct% + (专业/150×750)×major_pct%
    """
    full = MAJOR_FULL_SCORE.get(category, 300)
    
    # 处理 None 值：使用默认比例
    if culture_pct is None and major_pct is None:
        culture_pct, major_pct = DEFAULT_PCT.get(category, (50, 50))
    elif culture_pct is None:
        culture_pct = 0
    elif major_pct is None:
        major_pct = 0
    
    # 如果都为0，默认各50
    if culture_pct == 0 and major_pct == 0:
        culture_pct, major_pct = 50, 50
    
    # 专业分折算到750分制
    major_transformed = major / full * 750
    
    # 综合分
    score = culture * culture_pct / 100 + major_transformed * major_pct / 100
    return round(score, 1)


def estimate_probability(student_score, low_score, high_score):
    """
    估算录取概率
    学生综合分 vs 历史最低综合分 ~ 最高综合分
    """
    if student_score >= high_score:
        # 高于历史最高 → 非常稳妥
        diff = (student_score - high_score) / max(high_score - low_score, 10)
        prob = min(98, round(85 + diff * 5))
        return max(85, prob)
    elif student_score >= low_score:
        # 在历史区间内
        pos = (student_score - low_score) / max(high_score - low_score, 1)
        prob = round(35 + pos * 50)
        return max(30, min(85, prob))
    else:
        # 低于历史最低
        diff = (low_score - student_score) / max(high_score - low_score, 10)
        prob = round(30 - diff * 5)
        return max(1, prob)


def get_recommendations(culture, major, category):
    """
    获取艺术体育类推荐
    culture: 文化课分数
    major: 专业课分数
    category: 艺术类别（如'美术类'）
    wenli: '文科'或'理科'
    """
    data = load_data()
    if not data:
        return []
    
    results = []
    
    for item in data:
        # 类别筛选
        if item['category'] != category:
            continue
        
        culture_pct = item['culture_pct']
        major_pct = item['major_pct']
        low_score = item['low_score']
        high_score = item['high_score']
        
        if low_score is None or high_score is None:
            continue
        
        # 计算学生综合分
        student_score = calc_composite_score(culture, major, culture_pct, major_pct, category)
        
        # 估算概率
        prob = estimate_probability(student_score, low_score, high_score)
        
        results.append({
            'school': item['school'],
            'major': item['major'],
            'category': item['category'],
            'student_composite': student_score,
            'min_score': low_score,
            'max_score': high_score,
            'probability': prob,
            'culture_pct': culture_pct,
            'major_pct': major_pct,
        })
    
    # 按概率从高到低排序
    results.sort(key=lambda x: -x['probability'])
    
    return results


if __name__ == '__main__':
    # 测试
    import sys
    print(f'数据加载: {len(load_data())} 条')
    
    # 测试美术类：文化350 专业220
    recs = get_recommendations(350, 220, '美术类', '文科')
    print(f'\n美术类 文化350 专业220 推荐: {len(recs)} 条')
    for r in recs[:10]:
        print(f'  {r["school"]:25s} {r["major"]:20s} 综合分={r["student_composite"]:.0f} 历史{r["min_score"]:.0f}~{r["max_score"]:.0f} {r["probability"]}%')
    
    # 测试音乐类：文化380 专业160
    recs2 = get_recommendations(380, 160, '音乐类', '文科')
    print(f'\n音乐类 文化380 专业160 推荐: {len(recs2)} 条')
    for r in recs2[:10]:
        print(f'  {r["school"]:25s} {r["major"]:20s} 综合分={r["student_composite"]:.0f} 历史{r["min_score"]:.0f}~{r["max_score"]:.0f} {r["probability"]}%')
