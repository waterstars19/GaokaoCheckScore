"""
第四步：将 2025 专业组关联历年录取数据，计算每个专业组的预估标准化排位分段

策略：
  专业组内各专业 - 从历年数据中查找对应专业的标准化区间
  取组内所有专业区间的并集作为该专业组的预估区间
"""
import json
import os
from collections import defaultdict

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'processed')

GROUPS_FILE = os.path.join(OUTPUT_DIR, 'group_majors.json')
SCHOOL_STD_FILE = os.path.join(OUTPUT_DIR, 'school_standards.json')
MAJOR_STD_FILE = os.path.join(OUTPUT_DIR, 'major_standards.json')


def load_json(path, desc=''):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"  已加载 {desc}: {len(data['data'])} 条")
    return data['data']


def build_major_std_index(major_standards):
    """
    建立 (学校, 专业名称) → 历年标准化区间的索引
    返回: {(school, major): [(year, low_std, high_std), ...]}
    """
    index = defaultdict(list)
    for r in major_standards:
        key = (r['school'], r['major'])
        index[key].append((r['year'], r['low_std'], r['high_std']))
    return index


def build_school_std_index(school_standards):
    """
    建立 学校 → 历年标准化区间的索引
    返回: {school: [(year, low_std, high_std), ...]}
    """
    index = defaultdict(list)
    for r in school_standards:
        key = r['school']
        index[key].append((r['year'], r['low_std'], r['high_std']))
    return index


def merge_intervals(intervals):
    """
    合并多个区间为并集，取最低low和最高high
    intervals: [(low, high), ...]
    return: (merged_low, merged_high)
    """
    if not intervals:
        return None, None
    lows = [iv[0] for iv in intervals if iv[0] is not None]
    highs = [iv[1] for iv in intervals if iv[1] is not None]
    if not lows or not highs:
        return None, None
    return min(lows), max(highs)


def compute_group_standards():
    print("=" * 60)
    print("第四步：专业组 → 预估标准化区间")
    print("=" * 60)

    # 加载数据
    groups = load_json(GROUPS_FILE, '专业组')
    major_standards = load_json(MAJOR_STD_FILE, '专业标准化')
    school_standards = load_json(SCHOOL_STD_FILE, '学校标准化')

    major_index = build_major_std_index(major_standards)
    school_index = build_school_std_index(school_standards)

    print(f"\n关联专业组与历年数据...")
    group_results = []
    stats = {'matched_by_major': 0, 'matched_by_school': 0, 'no_match': 0}

    for g in groups:
        school = g['school']
        group_majors = [m['name'] for m in g['majors']]

        # 策略1：看组内各专业在历年的数据
        major_intervals = []
        matched_majors = set()
        for major_name in group_majors:
            major_key = (school, major_name)
            if major_key in major_index:
                for year, low, high in major_index[major_key]:
                    major_intervals.append((low, high))
                matched_majors.add(major_name)

        low_std, high_std = None, None

        if major_intervals:
            # 有专业级历史数据
            low_std, high_std = merge_intervals(major_intervals)
            if low_std is not None:
                stats['matched_by_major'] += 1

        if low_std is None:
            # 策略2：用该校整体数据作为兜底
            if school in school_index:
                school_intervals = [(low, high) for _, low, high in school_index[school]]
                low_std, high_std = merge_intervals(school_intervals)
                if low_std is not None:
                    stats['matched_by_school'] += 1

        if low_std is None:
            stats['no_match'] += 1

        group_results.append({
            'category': g['category'],
            'school': school,
            'group_code': g['group_code'],
            'major_count': g['major_count'],
            'subject_req': g['subject_req'],
            'matched_majors': len(matched_majors),
            'high_std': high_std,   # 门槛最高
            'low_std': low_std,     # 门槛最低
        })

    # 保存
    out_path = os.path.join(OUTPUT_DIR, 'group_standards.json')
    output = {
        'meta': {
            'description': '2025年专业组预估标准化排位分区间',
            'total_groups': len(group_results),
            'strategy': {
                'by_major': '组内专业历年数据合并',
                'by_school': '学校整体历年数据兜底',
            },
        },
        'data': group_results,
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n匹配统计:")
    print(f"  按专业匹配: {stats['matched_by_major']} 组")
    print(f"  按学校兜底: {stats['matched_by_school']} 组")
    print(f"  无匹配数据: {stats['no_match']} 组")

    # 示例
    has_data = [g for g in group_results if g['high_std'] is not None]
    print(f"\n专业组标准化示例:")
    for g in has_data[:3]:
        print(f"  {g['school']} {g['category']} 组{g['group_code']}: "
              f"预估区间 [{g['low_std']:,}~{g['high_std']:,}] "
              f"(匹配{g['matched_majors']}/{g['major_count']}个专业)")

    print(f"\n输出文件: {out_path}")
    print(f"第四步完成 ✅")
    print()
    return group_results


if __name__ == '__main__':
    compute_group_standards()
