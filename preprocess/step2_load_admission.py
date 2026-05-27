"""
第二步：读取历年录取数据，计算每个学校/专业的标准化排位分区间
"""
import json
import os
import glob
from collections import defaultdict

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'processed')
ADMISSION_PATTERN = os.path.join(PROJECT_DIR, '河南_*分_历年录取数据.json')
TOTAL_COUNTS_FILE = os.path.join(OUTPUT_DIR, 'total_counts.json')


def calc_standardized(rank, total):
    """标准化排位分（与step1保持相同公式）"""
    import math
    if total <= 0 or rank <= 0:
        return 0
    if rank > total:
        rank = total
    if rank == total:
        return 0
    ln_ratio = math.log(total / rank)
    ln_total = math.log(total)
    return round(ln_ratio / ln_total * 1_000_000)


def load_total_counts():
    with open(TOTAL_COUNTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_admission_data():
    """加载所有历年录取数据"""
    all_records = []
    for fp in sorted(glob.glob(ADMISSION_PATTERN)):
        filename = os.path.basename(fp)
        with open(fp, 'r', encoding='utf-8') as f:
            data = json.load(f)
        recs = data['data']
        all_records.extend(recs)
        print(f"  {filename}: {len(recs)} 条录取记录")
    print(f"  共 {len(all_records)} 条记录")
    return all_records


def compute_school_standards(records, total_counts):
    """
    计算各学校的标准化排位分区间
    
    对于每个学校，收集其所有专业的录取位次，取最高和最低位次
    """
    # 按 (year, school) 分组收集位次
    school_groups = defaultdict(list)
    for r in records:
        key = (r['year'], r['school'])
        rank = r.get('min_rank')
        if rank and rank > 0:
            school_groups[key].append(rank)

    results = []
    for (year, school), ranks in sorted(school_groups.items()):
        # 获取总人数
        cat = r.get('category', '理科')
        # 尝试找到该年的总人数
        # 我们需要从total_counts中查找
        total = _find_total(total_counts, year, cat)
        if total is None:
            continue

        high_rank = min(ranks)   # 最好排名（门槛最高）
        low_rank = max(ranks)    # 最差排名（门槛最低）

        high_std = calc_standardized(high_rank, total)
        low_std = calc_standardized(low_rank, total)

        results.append({
            'year': year,
            'school': school,
            'high_rank': high_rank,
            'low_rank': low_rank,
            'high_std': high_std,   # 门槛最高→排位分高
            'low_std': low_std,     # 门槛最低→排位分低
        })

    return results


def compute_major_standards(records, total_counts):
    """
    计算各(学校, 专业)的标准化排位分区间
    """
    major_groups = defaultdict(list)
    for r in records:
        key = (r['year'], r['school'], r.get('major', ''))
        rank = r.get('min_rank')
        if rank and rank > 0:
            major_groups[key].append(rank)

    results = []
    for (year, school, major), ranks in sorted(major_groups.items()):
        cat = '理科'  # 兼容旧数据
        total = _find_total(total_counts, year, cat)
        if total is None:
            cat = '文科'
            total = _find_total(total_counts, year, cat)
        if total is None:
            continue

        high_rank = min(ranks)
        low_rank = max(ranks)

        high_std = calc_standardized(high_rank, total)
        low_std = calc_standardized(low_rank, total)

        results.append({
            'year': year,
            'school': school,
            'major': major,
            'high_rank': high_rank,
            'low_rank': low_rank,
            'high_std': high_std,
            'low_std': low_std,
        })

    return results


CAT_TO_EN = {
    '理科': 'physics', '物理类': 'physics',
    '文科': 'history', '历史类': 'history',
}


def _find_total(total_counts, year, category):
    """从total_counts中查找对应年份科类的总人数"""
    year_str = str(year)
    if year_str not in total_counts:
        return None
    cat_data = total_counts[year_str]

    # 先将中文科类映射为英文
    mapped = CAT_TO_EN.get(category, category)
    if mapped in cat_data:
        return cat_data[mapped]

    # 兜底：尝试找该年任意数据
    if cat_data:
        return list(cat_data.values())[0]
    return None


def compute_admission_standards():
    print("=" * 60)
    print("第二步：历年录取数据标准化")
    print("=" * 60)

    total_counts = load_total_counts()
    print(f"总人数表已加载")

    records = load_admission_data()
    print()

    # 计算学校级
    school_results = compute_school_standards(records, total_counts)
    school_out = os.path.join(OUTPUT_DIR, 'school_standards.json')
    with open(school_out, 'w', encoding='utf-8') as f:
        json.dump({'meta': {'description': '各学校录取标准化排位分区间', 'count': len(school_results)},
                   'data': school_results}, f, ensure_ascii=False, indent=2)
    print(f"学校标准化区间: {len(school_results)} 条 → school_standards.json")

    # 计算专业级
    major_results = compute_major_standards(records, total_counts)
    major_out = os.path.join(OUTPUT_DIR, 'major_standards.json')
    with open(major_out, 'w', encoding='utf-8') as f:
        json.dump({'meta': {'description': '各专业录取标准化排位分区间', 'count': len(major_results)},
                   'data': major_results}, f, ensure_ascii=False, indent=2)
    print(f"专业标准化区间: {len(major_results)} 条 → major_standards.json")

    # 验证示例
    print(f"\n学校标准化示例:")
    for r in school_results[:3]:
        print(f"  {r['year']} {r['school']}: 位次[{r['high_rank']:,}~{r['low_rank']:,}] "
              f"→ 标准化[{r['low_std']:,}~{r['high_std']:,}]")

    print(f"\n第二步完成 ✅")
    print()
    return school_results, major_results


if __name__ == '__main__':
    compute_admission_standards()
