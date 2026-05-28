import pandas as pd
import json
import os
from collections import Counter

# Read the Excel
df = pd.read_excel(r'D:\Files\014数据文件夹\1647.全国大学院校信息专业介绍数据表\01.大学院校基础信息表（3237所大学）.xlsx')

print('Total records: {}'.format(len(df)))

# Classification helpers
def is_985(val):
    return pd.notna(val) and val == 985.0

def is_211(val):
    return pd.notna(val) and val == 211.0

def is_shuangyiliu(val):
    return pd.notna(val) and str(val) == '双一流'

def classify_level(row):
    if is_985(row['是否985']):
        return '985'
    if is_211(row['是否211']):
        return '211'
    if is_shuangyiliu(row['是否双一流']):
        return '双一流'
    if pd.notna(row['国重/省重']) and row['国重/省重'] == '国重点':
        return '国重点'
    if pd.notna(row['国重/省重']) and row['国重/省重'] == '省重点':
        return '省重点'
    return '普通'

def classify_level_type(row):
    if is_985(row['是否985']):
        yiliu = str(row['一流大学']) if pd.notna(row['一流大学']) else ''
        if 'A类' in yiliu:
            return '985(一流大学A类)'
        elif 'B类' in yiliu:
            return '985(一流大学B类)'
        elif '一流学科' in yiliu:
            return '985(一流学科)'
        return '985'
    if is_211(row['是否211']):
        if is_shuangyiliu(row['是否双一流']):
            yiliu = str(row['一流大学']) if pd.notna(row['一流大学']) else ''
            if 'B类' in yiliu:
                return '211(一流大学B类)'
            elif '一流学科' in yiliu:
                return '211(一流学科)'
            return '211(双一流)'
        return '211'
    if is_shuangyiliu(row['是否双一流']):
        yiliu = str(row['一流大学']) if pd.notna(row['一流大学']) else ''
        if '一流学科' in yiliu:
            return '双一流(一流学科)'
        return '双一流'
    return classify_level(row)

def classify_nature(val):
    if pd.isna(val) or val == '-':
        return '未知'
    val = str(val).strip()
    if val in ('公办',):
        return '公办'
    if val in ('民办',):
        return '民办'
    if val in ('中外合作办学', '内地与港澳台地区合作办学'):
        return '中外合作办学'
    return val

# Build the schools dict
schools = {}
duplicate_names = set()

for idx, row in df.iterrows():
    name = str(row['学校名称']).strip()
    if not name or name == 'nan' or name == 'NaN':
        continue
    
    level = classify_level(row)
    level_type = classify_level_type(row)
    nature = classify_nature(row['公私性质'])
    province = str(row['所在省']).strip() if pd.notna(row['所在省']) else ''
    city = str(row['城市']).strip() if pd.notna(row['城市']) else ''
    school_type = str(row['类型']).strip() if pd.notna(row['类型']) else ''
    benke_zhuanke = str(row['本科/专科']).strip() if pd.notna(row['本科/专科']) else ''
    
    entry = {
        'level': level,
        'level_detail': level_type,
        'nature': nature,
        'province': province,
        'city': city,
        'type': school_type,
        'degree': benke_zhuanke,
        'is_985': is_985(row['是否985']),
        'is_211': is_211(row['是否211']),
        'is_shuangyiliu': is_shuangyiliu(row['是否双一流']),
        'national_key': bool(pd.notna(row['国重/省重']) and row['国重/省重'] == '国重点'),
        'provincial_key': bool(pd.notna(row['国重/省重']) and row['国重/省重'] == '省重点'),
    }
    
    if name in schools:
        duplicate_names.add(name)
        continue
    
    schools[name] = entry

print()
print('Unique schools: {}'.format(len(schools)))
print('Duplicate name groups: {}'.format(len(duplicate_names)))

# Statistics
level_counts = Counter(s['level'] for s in schools.values())
nature_counts = Counter(s['nature'] for s in schools.values())
province_counts = Counter(s['province'] for s in schools.values())
degree_counts = Counter(s['degree'] for s in schools.values())
level_detail_counts = Counter(s['level_detail'] for s in schools.values())

print()
print('=' * 60)
print('  院校层次统计')
print('=' * 60)
for k in ['985', '211', '双一流', '国重点', '省重点', '普通']:
    print('  {:8s}: {:>5d}'.format(k, level_counts.get(k, 0)))

print()
print('  详细分类:')
for k, v in level_detail_counts.most_common():
    print('    {:30s}: {:>4d}'.format(k, v))

print()
print('=' * 60)
print('  办学性质统计')
print('=' * 60)
for k, v in nature_counts.most_common():
    print('  {:8s}: {:>5d}'.format(k, v))

print()
print('=' * 60)
print('  办学层次统计')
print('=' * 60)
for k, v in degree_counts.most_common():
    print('  {:4s}: {:>5d}'.format(k, v))

print()
print('=' * 60)
print('  省份分布 (Top 15)')
print('=' * 60)
for k, v in province_counts.most_common(15):
    print('  {:8s}: {:>4d}'.format(k, v))

# Output JSON
output_dir = r'D:\GoakaoProject\docs'
os.makedirs(output_dir, exist_ok=True)

output = {
    'meta': {
        'source': '01.大学院校基础信息表（3237所大学）.xlsx',
        'total_records': int(len(df)),
        'total_schools': len(schools),
        'total_duplicate_name_groups': len(duplicate_names),
        'fields': [
            'level', 'level_detail', 'nature', 'province', 'city', 
            'type', 'degree', 'is_985', 'is_211', 'is_shuangyiliu', 
            'national_key', 'provincial_key'
        ],
        'level_explanation': {
            '985': '985工程大学（含一流大学A类、B类、一流学科）',
            '211': '211工程大学（非985，含一流大学B类、一流学科建设）',
            '双一流': '双一流建设高校（非985/211的新晋双一流）',
            '国重点': '全国重点大学（非985/211/双一流）',
            '省重点': '省属重点大学',
            '普通': '普通院校'
        },
        'note': '数据可能不是最新版本。2022年第二轮双一流新增高校（如南方科技大学、上海科技大学等）可能未包含。建议定期更新数据源。',
        'statistics': {
            'by_level': dict(level_counts),
            'by_level_detail': dict(level_detail_counts.most_common()),
            'by_nature': dict(nature_counts),
            'by_degree': dict(degree_counts),
            'by_province_top15': dict(province_counts.most_common(15)),
            'summary': {
                '985_count': level_counts.get('985', 0),
                '211_count': level_counts.get('211', 0),
                'shuangyiliu_count': level_counts.get('双一流', 0),
                'national_key_count': level_counts.get('国重点', 0),
                'provincial_key_count': level_counts.get('省重点', 0),
                'normal_count': level_counts.get('普通', 0),
                'public_count': nature_counts.get('公办', 0),
                'private_count': nature_counts.get('民办', 0),
                'sino_foreign_count': nature_counts.get('中外合作办学', 0),
                'benke_count': degree_counts.get('本科', 0),
                'zhuanke_count': degree_counts.get('专科', 0),
            }
        }
    },
    'schools': schools
}

output_path = os.path.join(output_dir, 'school_metadata.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
print()
print('=' * 60)
print('  输出文件')
print('=' * 60)
print('  路径: {}'.format(output_path))
print('  大小: {:.2f} MB'.format(file_size_mb))

# Show representative examples
print()
print('=' * 60)
print('  代表性示例')
print('=' * 60)
examples = [
    '北京大学', '清华大学', '浙江大学',  # 985 一流大学A类
    '东北大学', '湖南大学',  # 985 一流大学B类
    '北京协和医学院',  # 985 一流学科
    '郑州大学', '云南大学', '新疆大学',  # 211 一流大学B类（晋升）
    '河南大学', '中国科学院大学', '宁波大学',  # 双一流（非211）
    '河南理工大学', '河南科技大学',  # 省重点
    '西安欧亚学院', '郑州工商学院',  # 民办本科
    '西交利物浦大学', '宁波诺丁汉大学',  # 中外合作
]
for name in examples:
    if name in schools:
        s = schools[name]
        print('  {:20s} | level={:6s} | detail={:20s} | nature={:6s} | {}'.format(
            name, s['level'], s['level_detail'], s['nature'], s['degree']))
    else:
        print('  {:20s} | NOT FOUND'.format(name))

print()
print('Done!')
