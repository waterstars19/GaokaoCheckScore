"""检查专业数据库中的重复条目"""
import json

with open(r'D:\GoakaoProject\processed\major_standards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

d = data['data']
print(f'类型: {type(d).__name__}, 长度: {len(d)}')

if isinstance(d, list):
    print(f'第一个: {json.dumps(d[0], ensure_ascii=False)[:500]}')
    
    # 检查所有条目的字段
    keys = set()
    for item in d[:100]:
        keys.update(item.keys())
    print(f'字段: {keys}')
    
    # 找带括号的
    name_count = 0
    tuition_count = 0
    chinese_paren_count = 0
    
    for item in d:
        name = item.get('name', '')
        if '(' in str(name):
            name_count += 1
        if '（' in str(name):
            chinese_paren_count += 1
        if '学费' in str(name) or '元' in str(name) or '学制' in str(name):
            tuition_count += 1
    
    print(f'\n带英文括号(): {name_count}')
    print(f'带中文括号（）: {chinese_paren_count}')
    
    # 打印带括号的示例
    print('\n=== 带括号的示例 (前20) ===')
    shown = 0
    for item in d:
        name = item.get('name', '')
        if '(' in str(name) or '（' in str(name):
            print(f'  {json.dumps(name, ensure_ascii=False)[:120]}')
            shown += 1
            if shown >= 20:
                break
    
    # 按学校+专业分组看重复
    print('\n=== 检查同一学校下同一专业的重复 ===')
    from collections import defaultdict
    school_major = defaultdict(list)
    for item in d:
        school = item.get('school', item.get('school_name', ''))
        name = item.get('name', '')
        key = f'{school}|{name}'
        school_major[key].append(item)
    
    # 找同一学校下名称相似（一个带括号一个不带）的
    print('按学校分组检查...')
    school_groups = defaultdict(list)
    for item in d:
        school = item.get('school', item.get('school_name', ''))
        name = item.get('name', '')
        # 去掉括号内容作为基准名
        import re
        base = re.sub(r'[（(][^）)]*[）)]', '', name).strip()
        school_groups[f'{school}|{base}'].append(item)
    
    dup_count = 0
    tuition_dup = 0
    for key, items in school_groups.items():
        if len(items) > 1:
            names_only = [it.get('name', '') for it in items]
            # 检查是否一个是纯名称，另一个带括号附加信息
            has_pure = any('(' not in n and '（' not in n for n in names_only)
            has_extra = any('(' in n or '（' in n for n in names_only)
            if has_pure and has_extra:
                tuition_dup += 1
                if dup_count < 10:
                    print(f'  重复: {key}')
                    for it in items:
                        n = it.get('name', '')
                        print(f'    - {n}')
                dup_count += 1
    
    print(f'\n共发现重复组: {dup_count}')
    
else:
    print(f'键: {list(d.keys())[:5]}')
