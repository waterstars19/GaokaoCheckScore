#!/usr/bin/env python3
"""
Clean admission_plans.json major field - optimized version.
Uses pure regex for speed with 500k+ records.
"""
import json
import re
import os
import sys
from collections import defaultdict

INPUT = r"D:\GoakaoProject\docs\admission_plans.json"
OUTPUT = r"D:\GoakaoProject\docs\admission_plans_cleaned.json"
REPORT = r"D:\GoakaoProject\docs\admission_plans_cleanup_report.json"

# ============================================================
# PRESERVED categories - keep these in major name
# ============================================================
PRESERVED_LIST = [
    '中外合作办学', '师范类', '师范',
    '实验班', '卓越班', '基地班', '创新班', '民族班',
    '定向', '免费', '国家专项', '地方专项',
]

# Build regex: match parens containing ONLY preserved keywords (with possible extra chars)
# e.g. （师范）, （中外合作办学）, (师范类)
def build_preserved_re():
    parts = []
    for kw in PRESERVED_LIST:
        # Escape for regex, match the keyword as a substring inside parens
        esc = re.escape(kw)
        parts.append(r'[（(]\s*' + esc + r'\s*[）)]')
    return re.compile('|'.join(parts))

PRESERVED_RE = build_preserved_re()

# ============================================================
# Extraction patterns
# ============================================================
# Tuition like: 5000元/年, 5000元/学年, 5000元/每学年
TUITION_RE = re.compile(r'(\d{3,6})\s*元\s*/\s*[每学年]')

# Duration like: 学制5年, 学制五年, 学制两年, 学制2年
DURATION_CN = {'一':'1','二':'2','三':'3','四':'4','五':'5','六':'6','七':'7','八':'8','九':'9','十':'10'}
DURATION_RE = re.compile(r'学制\s*(\d+|[一二三四五六七八九十]+)\s*年?')

# ============================================================
# Core cleaning function
# ============================================================
def clean_major(raw_major):
    """
    Returns (cleaned_major, direction, tuition, duration)
    """
    if not raw_major or not isinstance(raw_major, str):
        return raw_major, None, None, None
    
    major = raw_major.strip()
    original = major
    
    # Step 0: Normalize: half-width parens → full-width
    major = major.replace('(', '（').replace(')', '）')
    
    # Collapse double parens: （（xxx））→（xxx）. Repeat for nested cases.
    prev = None
    while major != prev:
        prev = major
        major = re.sub(r'（（([^（）]*?)））', r'（\1）', major)
    
    # Step 1: Extract all parenthesized segments
    all_parens = re.findall(r'[（][^（）]*[）]', major)
    
    if not all_parens:
        return major, None, None, None
    
    extracted_tuition = None
    extracted_duration = None
    directions = []
    
    # Step 2: Classify each parenthesized segment
    segments_to_remove = []
    
    for seg in all_parens:
        inner = seg[1:-1].strip()  # content between （ and ）
        
        # Check preserved
        inner_lower = inner.lower()
        is_preserved = False
        for kw in PRESERVED_LIST:
            if kw.lower() in inner_lower:
                # Be more specific: the keyword should be a significant part of the content
                if len(inner_lower) <= len(kw) + 15:
                    is_preserved = True
                    break
        
        if is_preserved:
            continue
        
        # Check tuition
        tm = TUITION_RE.search(inner)
        if tm:
            extracted_tuition = int(tm.group(1))
            segments_to_remove.append(seg)
            # Check remaining content after tuition removal
            remaining = TUITION_RE.sub('', inner).strip('；;，, 　')
            if remaining and len(remaining) > 1:
                # It's probably a location/direction note - discard
                pass
            continue
        
        # Check duration
        dm = DURATION_RE.search(inner)
        if dm:
            dur = dm.group(1)
            if dur in DURATION_CN:
                dur = DURATION_CN[dur]
            extracted_duration = dur
            segments_to_remove.append(seg)
            continue
        
        # Check direction keywords
        if re.search(r'(方向|特色|模块|培养|国际)$', inner):
            directions.append(inner)
            segments_to_remove.append(seg)
            continue
        
        # Check junk indicators
        junk_pattern = re.compile(
            r'办学地点|只招|不招|色盲|色弱|语种|学费|元/年|元/学|收费标准|'
            r'招生章程|咨询院校|单列专业|应用科技学院|软件类|特殊培养|'
            r'嵌入式培养|少数民族|全科教师|免费全科|国家免费|免费医学|'
            r'联合培养|双语班|中外课程|国家级一流|马来西亚|学制|'
            r'注册会计师|管理会计|跨境电商|注册师|男生|女生|'
            r'5\+3|指挥类|非指挥'
        )
        if junk_pattern.search(inner):
            segments_to_remove.append(seg)
            continue
        
        # Pure numbers like "2"
        if re.match(r'^\d+$', inner):
            segments_to_remove.append(seg)
            continue
        
        # Something else - treat as direction if short
        if len(inner) <= 40:
            directions.append(inner)
            segments_to_remove.append(seg)
        else:
            # Long text - junk
            segments_to_remove.append(seg)
    
    # Step 3: Remove junk segments from major string
    cleaned = major
    for seg in segments_to_remove:
        cleaned = cleaned.replace(seg, '', 1)
    
    # Clean up artifacts
    cleaned = re.sub(r'（\s*）', '', cleaned)  # empty parens
    cleaned = re.sub(r'\s+', '', cleaned)
    # Remove double punctuation
    cleaned = re.sub(r'；；+', '', cleaned)
    
    if not cleaned:
        cleaned = original
    
    direction = '；'.join(directions) if directions else None
    
    return cleaned, direction, extracted_tuition, extracted_duration


def main():
    print("=" * 60)
    print("Admission Plans Major Field Cleaner v2")
    print("=" * 60)
    
    # --- LOAD ---
    print(f"\n[1/5] Loading data...")
    with open(INPUT, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    
    records = raw['data']
    meta = raw['meta']
    total_before = len(records)
    print(f"  Loaded {total_before:,} records")
    
    # --- CLEAN ---
    print(f"\n[2/5] Cleaning major fields...")
    parens_cleaned = 0
    tuition_extracted = 0
    direction_extracted = 0
    cleaned_records = []
    
    batch_size = 50000
    for i, rec in enumerate(records):
        major = rec.get('major', '')
        cleaned, direction, tuition_val, duration_val = clean_major(major)
        
        new_rec = dict(rec)
        
        if cleaned != major:
            parens_cleaned += 1
        new_rec['major'] = cleaned
        
        if direction:
            new_rec['direction'] = direction
            direction_extracted += 1
        
        if tuition_val is not None:
            existing = rec.get('tuition')
            if existing is None or existing == '' or existing == 0:
                new_rec['tuition'] = tuition_val
                tuition_extracted += 1
        
        if duration_val is not None:
            existing = rec.get('duration', '')
            if existing in (None, '', '-', '0'):
                new_rec['duration'] = duration_val
        
        cleaned_records.append(new_rec)
        
        if (i + 1) % batch_size == 0:
            print(f"  Processed {i+1:,} / {total_before:,} records...")
    
    print(f"  Done! Parens cleaned: {parens_cleaned:,}, Tuitions: {tuition_extracted:,}, Directions: {direction_extracted:,}")
    
    # --- MERGE ---
    print(f"\n[3/5] Merging duplicates within same year+school+code...")
    
    # Group by (year, school, school_code, major_code, major)
    groups = defaultdict(list)
    for rec in cleaned_records:
        key = (
            rec.get('year'),
            rec.get('school', ''),
            rec.get('school_code', ''),
            rec.get('major_code', ''),
            rec.get('major', ''),
        )
        groups[key].append(rec)
    
    merged_records = []
    duplicates_removed = 0
    
    for key, group in groups.items():
        if len(group) == 1:
            merged_records.append(group[0])
        else:
            merged = dict(group[0])
            total_planned = sum(r.get('planned_count') or 0 for r in group)
            merged['planned_count'] = total_planned
            merged_records.append(merged)
            duplicates_removed += len(group) - 1
    
    total_after = len(merged_records)
    print(f"  Groups: {len(groups):,}, Merged records: {total_after:,}, Removed: {duplicates_removed:,}")
    
    # --- SHOW EXAMPLES ---
    print(f"\n[4/5] Sample transformations:")
    seen = set()
    count = 0
    for rec in records:
        major = rec.get('major', '')
        cleaned, direction, _, _ = clean_major(major)
        if cleaned != major:
            pair = (major, cleaned)
            if pair not in seen:
                seen.add(pair)
                print(f"  [{major}] → [{cleaned}]" + (f" dir=[{direction}]" if direction else ""))
                count += 1
                if count >= 25:
                    break
    
    # --- SAVE ---
    print(f"\n[5/5] Saving results...")
    
    output_data = {
        'meta': {
            **meta,
            'cleaned_at': '2026-05-28T16:04:00+08:00',
            'records_before_cleaning': total_before,
            'records_after_cleaning': total_after,
            'duplicates_removed_in_merge': duplicates_removed,
            'parens_cleaned_count': parens_cleaned,
            'tuition_extracted_count': tuition_extracted,
            'direction_extracted_count': direction_extracted,
        },
        'data': merged_records
    }
    
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False)
    output_size = os.path.getsize(OUTPUT)
    
    report = {
        'total_before': total_before,
        'total_after': total_after,
        'duplicates_removed': duplicates_removed,
        'parentheses_cleaned': parens_cleaned,
        'tuition_extracted': tuition_extracted,
        'direction_extracted': direction_extracted,
        'dedup_rate_pct': round(duplicates_removed / total_before * 100, 2),
        'clean_rate_pct': round(parens_cleaned / total_before * 100, 2),
        'output_file': OUTPUT,
        'output_size_mb': round(output_size / 1024 / 1024, 2),
    }
    
    with open(REPORT, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("CLEANUP COMPLETE")
    print("=" * 60)
    for k, v in report.items():
        if isinstance(v, float):
            print(f"  {k}: {v}")
        else:
            print(f"  {k}: {v:,}")
    print("=" * 60)


if __name__ == '__main__':
    main()
