#!/usr/bin/env python3
"""
Clean admission_plans.json major field - v3 (comprehensive).
Handles: parenthesized junk, unparenthesized location/tuition, double-parens.
"""
import json
import re
import os
from collections import defaultdict

INPUT = r"D:\GoakaoProject\docs\admission_plans.json"
OUTPUT = r"D:\GoakaoProject\docs\admission_plans_cleaned.json"
REPORT = r"D:\GoakaoProject\docs\admission_plans_cleanup_report.json"

# ============================================================
# PRESERVED categories
# ============================================================
PRESERVED_LIST = [
    '中外合作办学', '师范类', '师范',
    '实验班', '卓越班', '基地班', '创新班', '民族班',
    '定向', '免费', '国家专项', '地方专项',
]

# ============================================================
# Extraction patterns
# ============================================================
TUITION_RE = re.compile(r'(\d{3,6})\s*元\s*/\s*[每学年]')
DURATION_CN = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
               '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'}
DURATION_RE = re.compile(r'学制\s*(\d+|[一二三四五六七八九十]+)\s*年?')

# Junk keywords that appear INSIDE parentheses
JUNK_IN_PATTERN = re.compile(
    r'办学地点|只招|不招|色盲|色弱|语种|学费|元/年|元/学|收费标准|'
    r'招生章程|咨询院校|单列专业|应用科技学院|软件类|特殊培养|'
    r'嵌入式培养|少数民族|全科教师|免费全科|国家免费|免费医学|'
    r'联合培养|双语班|中外课程|国家级一流|马来西亚|'
    r'5\+3|指挥类|非指挥|包含专业|含',
    re.IGNORECASE
)

# Junk suffixes that appear OUTSIDE parentheses
# Pattern: 专业名办学地点：xxx, 专业名包含专业：xxx, etc.
JUNK_SUFFIX_RE = re.compile(
    r'[，,；;。.]?\s*('
    r'办学地点[：:][^（）()]*(?=$|[（(])|'
    r'包含专业[：:][^（）()]*(?=$|[（(])|'
    r'学费[^（）()]*(?=$|[（(])|'
    r'收费标准[^（）()]*(?=$|[（(])'
    r')',
    re.IGNORECASE
)


def is_preserved(inner):
    """Check if parenthesized content is a preserved modifier."""
    inner_lower = inner.strip().lower()
    for kw in PRESERVED_LIST:
        if kw.lower() in inner_lower:
            # Must be a significant portion (keyword is at least 50% of content)
            if len(kw) >= len(inner_lower) * 0.3:
                return True
    return False


def normalize_parens(s):
    """Collapse double parens: （（xxx））→（xxx）. Handle nested."""
    prev = None
    while s != prev:
        prev = s
        # （（xxx）） → （xxx）
        s = re.sub(r'（（([^（）]*?)））', r'（\1）', s)
        # （（xxx）  (unclosed double) → （xxx
        s = re.sub(r'（（([^（）]*?)）(?!）)', r'（\1', s)
    return s


def clean_major(raw_major):
    """
    Clean a single major string.
    Returns (cleaned_major, direction, tuition, duration)
    """
    if not raw_major or not isinstance(raw_major, str):
        return raw_major, None, None, None
    
    major = raw_major.strip()
    if not major:
        return '', None, None, None
    
    original = major
    
    # Step 0: Normalize
    major = major.replace('(', '（').replace(')', '）')
    major = normalize_parens(major)
    
    extracted_tuition = None
    extracted_duration = None
    directions = []
    
    # Step 1: Extract all parenthesized segments (non-overlapping, from outside-in)
    all_parens = []
    # Find all parenthesized segments using simple regex
    for m in re.finditer(r'（[^（）]*?）', major):
        all_parens.append((m.start(), m.end(), m.group()))
    
    # Step 2: Classify each segment
    segments_to_remove = []
    
    for start, end, seg in all_parens:
        inner = seg[1:-1].strip()
        
        if is_preserved(inner):
            continue
        
        # Try tuition extraction
        tm = TUITION_RE.search(inner)
        if tm:
            extracted_tuition = int(tm.group(1))
            segments_to_remove.append(seg)
            continue
        
        # Try duration extraction
        dm = DURATION_RE.search(inner)
        if dm:
            dur = dm.group(1)
            if dur in DURATION_CN:
                dur = DURATION_CN[dur]
            extracted_duration = dur
            segments_to_remove.append(seg)
            continue
        
        # Check direction keywords
        if re.search(r'(方向|特色|模块|培养)$', inner):
            directions.append(inner)
            segments_to_remove.append(seg)
            continue
        
        # Check junk keywords
        if JUNK_IN_PATTERN.search(inner):
            segments_to_remove.append(seg)
            continue
        
        # Pure numbers
        if re.match(r'^\d+$', inner):
            segments_to_remove.append(seg)
            continue
        
        # Short content → direction
        if len(inner) <= 40:
            directions.append(inner)
            segments_to_remove.append(seg)
        else:
            segments_to_remove.append(seg)
    
    # Step 3: Remove segments from major
    cleaned = major
    # Remove from end to start to preserve indices
    for seg in sorted(set(segments_to_remove), key=lambda x: -len(x)):
        cleaned = cleaned.replace(seg, '', 1)
    
    # Step 4: Remove unparenthesized junk suffixes
    cleaned = JUNK_SUFFIX_RE.sub('', cleaned)
    
    # Step 5: Clean up artifacts
    cleaned = re.sub(r'（\s*）', '', cleaned)      # empty parens
    cleaned = re.sub(r'\s+', '', cleaned)          # whitespace
    cleaned = re.sub(r'[；;，,。.]+$', '', cleaned) # trailing punctuation
    cleaned = cleaned.strip()
    
    if not cleaned:
        cleaned = original
    
    direction = '；'.join(directions) if directions else None
    
    return cleaned, direction, extracted_tuition, extracted_duration


def make_key(record):
    return (
        record.get('year'),
        record.get('school', ''),
        record.get('school_code', ''),
        record.get('major_code', ''),
        record.get('major', ''),
    )


def main():
    print("=" * 60)
    print("Admission Plans Major Field Cleaner v3")
    print("=" * 60)
    
    # --- LOAD ---
    print(f"\n[1/5] Loading data from {INPUT}...")
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
            print(f"  Processed {i+1:,} / {total_before:,}")
    
    print(f"  Done! Parens: {parens_cleaned:,}, Tuitions: {tuition_extracted:,}, Directions: {direction_extracted:,}")
    
    # --- MERGE ---
    print(f"\n[3/5] Merging duplicates by (year, school, school_code, major_code, major)...")
    
    groups = defaultdict(list)
    for rec in cleaned_records:
        key = make_key(rec)
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
    print(f"  Groups: {len(groups):,}, After merge: {total_after:,}, Removed: {duplicates_removed:,}")
    
    # --- QUALITY CHECK ---
    print(f"\n[4/5] Quality checks...")
    
    # Count remaining issues
    double_paren = sum(1 for r in merged_records if '（（' in r.get('major', ''))
    junk_left = sum(1 for r in merged_records if '办学地点' in r.get('major', '') or '元/年' in r.get('major', ''))
    empty_major = sum(1 for r in merged_records if not r.get('major', '').strip())
    
    print(f"  Double parens remaining: {double_paren}")
    print(f"  Location/tuition junk remaining: {junk_left}")
    print(f"  Empty majors: {empty_major}")
    
    # Sample transformations
    print(f"\n  Sample transformations (first 30):")
    seen = set()
    count = 0
    for rec in records:
        major = rec.get('major', '')
        cleaned, direction, _, _ = clean_major(major)
        if cleaned != major:
            pair = (major, cleaned)
            if pair not in seen:
                seen.add(pair)
                extra = f" dir=[{direction}]" if direction else ""
                print(f"    [{major[:80]}{'...' if len(major)>80 else ''}] → [{cleaned}]{extra}")
                count += 1
                if count >= 30:
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
            'double_parens_remaining': double_paren,
            'junk_remaining': junk_left,
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
        'remaining_issues': {
            'double_parens': double_paren,
            'junk_in_major': junk_left,
            'empty_majors': empty_major,
        },
        'output_file': OUTPUT,
        'output_size_mb': round(output_size / 1024 / 1024, 2),
    }
    
    with open(REPORT, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("CLEANUP COMPLETE")
    print("=" * 60)
    print(f"  Records before:  {total_before:>10,}")
    print(f"  Records after:   {total_after:>10,}")
    print(f"  Dups removed:    {duplicates_removed:>10,}")
    print(f"  Parens cleaned:  {parens_cleaned:>10,}")
    print(f"  Tuitions found:  {tuition_extracted:>10,}")
    print(f"  Directions:      {direction_extracted:>10,}")
    print(f"  Output size:     {output_size/1024/1024:>10.1f} MB")
    print(f"  Output: {OUTPUT}")
    print(f"  Report: {REPORT}")
    print("=" * 60)


if __name__ == '__main__':
    main()
