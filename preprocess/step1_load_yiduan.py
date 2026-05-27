"""
第一步：读取一分一段表，计算每个(年份, 科类, 分数)的标准化排位分区间
"""
import json
import os
import math
from collections import defaultdict

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'processed')
YIDUAN_FILE = os.path.join(PROJECT_DIR, '河南一分一段表_2017-2025.json')


def calc_standardized(rank, total):
    """
    标准化排位分计算公式：
    standardized = ln(N / rank) / ln(N) × 1,000,000
    """
    if total <= 0 or rank <= 0:
        return 0
    if rank > total:
        rank = total
    if rank == total:
        return 0
    # ln(N/rank) / ln(N) 先算比值再乘100万
    ln_ratio = math.log(total / rank)
    ln_total = math.log(total)
    return round(ln_ratio / ln_total * 1_000_000)


def compute_yiduan_standards():
    """读取一分一段表，为每个分数计算标准化排位分区间"""
    print("=" * 60)
    print("第一步：一分一段表标准化")
    print("=" * 60)

    with open(YIDUAN_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    records = data['data']
    print(f"原始记录数: {len(records)}")

    # 1. 计算每个 (year, cat) 的总人数
    total_counts = defaultdict(int)
    for r in records:
        key = (r['year'], r['category'])
        # 总人数 = 最低分数的累计人数
        # 取该 (year, cat) 的最大 cumulative
        if r['cumulative'] > total_counts[key]:
            total_counts[key] = r['cumulative']

    print(f"\n各年份-科类总人数:")
    for (y, c), n in sorted(total_counts.items(), reverse=True):
        print(f"  {y} {c}: {n:,} 人")

    # 保存总人数
    total_counts_output = {}
    for (y, c), n in total_counts.items():
        year_key = str(y)
        if year_key not in total_counts_output:
            total_counts_output[year_key] = {}
        total_counts_output[year_key][c] = n

    with open(os.path.join(OUTPUT_DIR, 'total_counts.json'), 'w', encoding='utf-8') as f:
        json.dump(total_counts_output, f, ensure_ascii=False, indent=2)
    print(f"\n总人数已保存: total_counts.json")

    # 2. 按 (year, cat, score) 分组，计算每个分数的标准化区间
    # 先把记录按分数分组
    score_groups = defaultdict(list)
    for r in records:
        key = (r['year'], r['category'], r['score'])
        score_groups[key] = r  # 每个分数只有一条记录（已去重）

    standards = []
    for r in records:
        year = r['year']
        cat = r['category']
        score = r['score']
        count_people = r['count']
        cumulative = r['cumulative']

        total = total_counts.get((year, cat), 0)
        if total == 0:
            continue

        # 计算考生区间
        # 最高位次（最好排名）= cumulative - count_people + 1
        # 最低位次（最差排名）= cumulative
        high_rank = cumulative - count_people + 1  # 同分中最好排名，数字最小
        low_rank = cumulative                      # 同分中最差排名，数字最大

        if high_rank < 1:
            high_rank = 1

        # 高排位分（数值大）← 用最高位次（rank小）计算
        high_std = calc_standardized(high_rank, total)
        # 低排位分（数值小）← 用最低位次（rank大）计算
        low_std = calc_standardized(low_rank, total)

        standards.append({
            'year': year,
            'category': cat,
            'score': score,
            'count': count_people,
            'cumulative': cumulative,
            'high_rank': high_rank,
            'low_rank': low_rank,
            'high_std': high_std,   # 最好情况（排位分高）
            'low_std': low_std,     # 最差情况（排位分低）
        })

    # 排序：年份降序、科类、分数降序
    cat_order = {'history': 0, 'physics': 1}
    standards.sort(key=lambda x: (-x['year'], cat_order.get(x['category'], 0), -x['score']))

    output = {
        'meta': {
            'description': '河南高考标准化排位分查找表',
            'formula': 'standardized = ln(N/rank) / ln(N) × 1,000,000',
            'total_records': len(standards),
        },
        'data': standards,
    }

    out_path = os.path.join(OUTPUT_DIR, 'standardized_scores.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 验证
    print(f"\n标准化排位分示例:")
    for r in standards[:5]:
        print(f"  {r['year']} {r['category']} {r['score']}分: "
              f"位次[{r['high_rank']:,}~{r['low_rank']:,}] "
              f"→ 标准化[{r['low_std']:,}~{r['high_std']:,}]")

    # 检查范围
    all_stds = [r['high_std'] for r in standards] + [r['low_std'] for r in standards]
    print(f"\n标准化排位分范围: {min(all_stds):,} ~ {max(all_stds):,}")
    print(f"输出文件: {out_path}")
    print(f"总记录数: {len(standards)}")
    print("第一步完成 ✅")
    print()

    return standards, total_counts


if __name__ == '__main__':
    compute_yiduan_standards()
