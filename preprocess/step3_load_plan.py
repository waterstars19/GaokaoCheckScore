"""
第三步：读取 2025 年招生计划，提取专业组结构
"""
import json
import os
import pandas as pd
from collections import defaultdict, OrderedDict

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'processed')
PLAN_FILE = os.path.join(PROJECT_DIR, '招生计划', '20250621-河南-2025-招生计划.xlsx')


def load_plan():
    print("=" * 60)
    print("第三步：2025 招生计划 - 专业组结构提取")
    print("=" * 60)

    df = pd.read_excel(PLAN_FILE, header=1)
    print(f"原始行数: {len(df)}")

    # 清理列名
    df = df.rename(columns={
        '院校名称': 'school',
        '专业组代码': 'group_code',
        '专业代码': 'major_code',
        '专业名称': 'major',
        '科类': 'category',
        '批次': 'batch',
        '选科要求': 'subject_req',
        '学制': 'duration',
        '学费': 'tuition',
        '计划人数': 'plan_count',
        '专业备注': 'remark',
        '院校代码': 'school_code',
    })

    # 只保留本科批
    df = df[df['batch'] == '本科批'].copy()
    print(f"本科批: {len(df)} 行")

    # ========== 专业组结构 ==========
    # 按 (科类, 学校, 专业组代码) 分组，列出组内所有专业
    print("\n提取专业组结构...")

    groups = OrderedDict()
    group_records = df.groupby(['category', 'school', 'group_code'])

    for (cat, school, gcode), grp in group_records:
        gkey = f"{cat}|{school}|{gcode}"
        majors = []
        for _, row in grp.iterrows():
            majors.append({
                'code': str(row['major_code']),
                'name': row['major'],
                'subject_req': row.get('subject_req', ''),
                'remark': row.get('remark', ''),
                'plan_count': int(row.get('plan_count', 0)),
            })

        groups[gkey] = {
            'category': cat,
            'school': school,
            'group_code': str(gcode),
            'major_count': len(majors),
            'subject_req': grp['subject_req'].iloc[0],  # 组内选科要求通常一致
            'majors': majors,
        }

    # 转为列表输出
    groups_list = list(groups.values())

    # 统计
    cat_counts = defaultdict(int)
    size_dist = defaultdict(int)
    for g in groups_list:
        cat_counts[g['category']] += 1
        size_dist[g['major_count']] += 1

    print(f"\n专业组统计:")
    for cat, cnt in sorted(cat_counts.items()):
        print(f"  {cat}: {cnt} 组")
    print(f"  合计: {len(groups_list)} 组")

    print(f"\n专业组大小分布:")
    small = sum(v for k, v in size_dist.items() if k <= 6)
    large = sum(v for k, v in size_dist.items() if k > 6)
    print(f"  ≤6 个专业: {small} 组 ({small/len(groups_list)*100:.1f}%)")
    print(f"  >6 个专业: {large} 组 ({large/len(groups_list)*100:.1f}%)")

    # 保存专业组→专业列表
    out_path = os.path.join(OUTPUT_DIR, 'group_majors.json')
    output = {
        'meta': {
            'description': '2025年河南高考招生计划-专业组结构',
            'total_groups': len(groups_list),
        },
        'data': groups_list,
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n输出文件: {out_path}")

    # 示例
    print(f"\n专业组示例:")
    for g in groups_list[:3]:
        majors_preview = [m['name'] for m in g['majors'][:6]]
        suffix = '...' if g['major_count'] > 6 else ''
        print(f"  {g['school']} {g['category']} 组{g['group_code']}: "
              f"{g['major_count']}个专业 → {', '.join(majors_preview)}{suffix}")

    print(f"\n第三步完成 ✅")
    print()
    return groups_list


if __name__ == '__main__':
    load_plan()
