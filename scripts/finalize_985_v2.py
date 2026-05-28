# -*- coding: utf-8 -*-
"""Finalize 985 school data extraction - improved version."""
import openpyxl
import json
import re
from datetime import datetime
import os

XLSX_PATH = r'D:\Files\014数据文件夹\1647.全国大学院校信息专业介绍数据表\01.大学院校基础信息表（3237所大学）.xlsx'
META_PATH = r'D:\GoakaoProject\docs\school_metadata.json'
OUTPUT_PATH = r'D:\GoakaoProject\data_985\985_schools_local.json'


def extract_colleges(text, school_name):
    """Extract college names from university introduction text."""
    if not text or text == 'None':
        return []
    colleges = set()
    
    # Direct structured pattern: "共有X个学院 / 学部"
    for match in re.finditer(r'(?:设有|下设|共有|现有|包含|涵盖|包括)(\d+)个(?:学院|学部|院系)[：:，,]([^。]{10,600})', text):
        content = match.group(2)
        # Extract all xxx学院 / xxx学部
        for n in re.findall(r'[\u4e00-\u9fff]{2,8}(?:学院|学部)', content):
            n = clean_name(n)
            if n and n not in ['个学院', '个学部'] and len(re.findall(r'[\u4e00-\u9fff]', n)) >= 3:
                colleges.add(n)
    
    # Direct listing pattern: "A学院、B学院、C学院" 
    for match in re.finditer(r'[\u4e00-\u9fff]{2,8}学院[、，,][\u4e00-\u9fff]{2,8}学院', text):
        for n in re.findall(r'[\u4e00-\u9fff]{2,8}学院', match.group()):
            n = clean_name(n)
            if n and len(re.findall(r'[\u4e00-\u9fff]', n)) >= 3:
                colleges.add(n)
    
    # "XX学部" enumeration
    for match in re.finditer(r'[\u4e00-\u9fff]{2,8}学部[，、,][\u4e00-\u9fff]{2,8}学部', text):
        for n in re.findall(r'[\u4e00-\u9fff]{2,8}学部', match.group()):
            n = clean_name(n)
            if n and len(re.findall(r'[\u4e00-\u9fff]', n)) >= 2:
                colleges.add(n)
    
    # Individual well-formed mentions
    for match in re.finditer(r'(?:设有|下设|包括|涵盖|包含|拥有|现有)(\d*个?)([\u4e00-\u9fff]{2,8}(?:学院|学部))', text):
        n = clean_name(match.group(2))
        if n and len(re.findall(r'[\u4e00-\u9fff]', n)) >= 3:
            colleges.add(n)
    
    # Also extract from 华东师范大学 style: "学部：X、Y、Z；X个全日制学院：A、B"
    sections = re.split(r'[；;]', text)
    for section in sections:
        if '学院' in section or '学部' in section:
            for n in re.findall(r'[\u4e00-\u9fff]{2,8}(?:学院|学部)', section):
                n = clean_name(n)
                if n and len(re.findall(r'[\u4e00-\u9fff]', n)) >= 3:
                    colleges.add(n)
    
    # Filter
    result = []
    for c in colleges:
        if is_valid_college(c, school_name):
            result.append(c)
    
    return sorted(set(result))


def clean_name(n):
    """Clean up extracted college name."""
    n = n.strip()
    # Remove digit prefix
    n = re.sub(r'^\d+个', '', n)
    n = re.sub(r'^\d+', '', n)
    return n


def is_valid_college(name, school_name):
    """Check if the name is a valid college."""
    skip_list = [
        '个学院', '个学部', '个专业学院', '个独立建制的学院',
        '中国科学院', '中国工程院', '中国社会科学院',
        '欧洲科学院', '美国科学院', '英国皇家', '加拿大皇家',
        '发展中国家科学院', '第三世界科学院',
        '俄罗斯', '欧洲文理', '国际量子',
        '与中央', '立第四', '独立为', '度名为',
        '个中外合作办学学院', '个工程师学院',
        '个国际化合作', '法五大',
        '校友中', '教师中有', '教师中',
        '其中包括', '兄弟高校',
        '在全国', '学校有', '其中的', '部分在北',
        '个学科型', '所独立',
        '以其工', '将其工',
        '与天津', '与北平', '与河北',
        '等试验班',
        '求恢复',
        '合组国立',
        '原国立', '原址建立', '原长沙',
        '已与美国', '已与瑞典',
        '个专业',
        '个二级',
        '个专门',
        '个国际化示范',
        '年学校与',
    ]
    for s in skip_list:
        if s in name:
            return False
    
    # Must have >=3 Chinese chars
    chinese = re.findall(r'[\u4e00-\u9fff]', name)
    if len(chinese) < 3:
        return False
    
    return True


def extract_majors(raw):
    """Extract deduplicated major list."""
    if not raw or raw == 'None' or not raw.strip():
        return []
    seen = set()
    result = []
    for m in raw.split(';'):
        m = m.strip().strip('"').strip("'")
        if m and len(m) > 1 and m not in seen:
            seen.add(m)
            result.append(m)
    return result


# ========== Main ==========
with open(META_PATH, 'r', encoding='utf-8') as f:
    meta_data = json.load(f)
schools_meta = meta_data.get('schools', {})
school_985_names = set()
for name, info in schools_meta.items():
    if info.get('is_985'):
        school_985_names.add(name)

print(f"985 schools: {len(school_985_names)}")

wb = openpyxl.load_workbook(XLSX_PATH, read_only=True)
ws = wb.active

results = []
for row in ws.iter_rows(min_row=2, values_only=True):
    if not row[0]:
        continue
    xname = str(row[0]).strip()
    if xname not in school_985_names:
        continue
    
    major_list = extract_majors(str(row[15]) if row[15] else '')
    college_list = extract_colleges(str(row[30]) if row[30] else '', xname)
    
    results.append({
        'school_name': xname,
        'college_list': college_list,
        'major_list': major_list,
        'source_file': '01.大学院校基础信息表（3237所大学）.xlsx'
    })

results.sort(key=lambda x: x['school_name'])

output = {
    'meta': {
        'source': 'local_folder',
        'scanned_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'data_source': '01.大学院校基础信息表（3237所大学）.xlsx',
        'total_985_schools': len(results)
    },
    'schools': results
}

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'Written: {OUTPUT_PATH}')

maj_tot = sum(len(s['major_list']) for s in results)
col_tot = sum(len(s['college_list']) for s in results)
maj_s = sum(1 for s in results if s['major_list'])
col_s = sum(1 for s in results if s['college_list'])

print(f'\n=== Summary ===')
print(f'985 schools covered: {len(results)}')
print(f'With majors: {maj_s} ({maj_tot} total)')
print(f'With colleges: {col_s} ({col_tot} total)')
print(f'\nSchools with colleges:')
for s in results:
    if s['college_list']:
        print(f'  {s["school_name"]}: {s["college_list"]}')
