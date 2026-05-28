#!/usr/bin/env python3
"""
Clean admission_plans.json major field:
- Remove junk parenthetical info (tuition, location, restrictions, etc.)
- Preserve important modifiers (师范, 中外合作办学, 实验班, etc.)
- Extract tuition and duration from parentheses
- Merge duplicates by (year, school, school_code, major_code) preserving variants
"""
import json
import re
import sys
from collections import defaultdict, Counter

INPUT = r"D:\GoakaoProject\docs\admission_plans.json"
OUTPUT = r"D:\GoakaoProject\docs\admission_plans_cleaned.json"
REPORT = r"D:\GoakaoProject\docs\admission_plans_cleanup_report.json"

# ============================================================
# PRESERVED PARENTHETICAL MODIFIERS
# When any of these appear in parentheses, keep them attached to the major name.
# ============================================================
PRESERVED_PATTERNS = [
    # Full-width Chinese parens
    r'中外合作办学',
    r'师范类?',
    r'实验班',
    r'卓越班',
    r'基地班',
    r'创新班',
    r'民族班',
    r'定向(?!就业)',      # 定向 but not 定向就业
    r'免费(?![^）)]*定向)', # 免费 but not 免费...定向
    r'国家专项',
    r'地方专项',
    # Half-width
    r'中外合作办学',
    r'师范类?',
    r'实验班',
    r'卓越班',
    r'基地班',
    r'创新班',
    r'民族班',
    r'定向',
    r'免费',
    r'国家专项',
    r'地方专项',
]

# Compile PRESERVED regex: match any of the preserved types (case-insensitive, space-insensitive-ish)
PRESERVED_RE = re.compile(
    r'[（(]\s*(' + '|'.join(PRESERVED_PATTERNS) + r')[^）)]*[）)]',
    re.IGNORECASE
)

# Also compile a more specific "match only preserved" for extraction
PRESERVED_SIMPLE = {
    '中外合作办学', '师范', '师范类', '实验班', '卓越班', '基地班',
    '创新班', '民族班', '定向', '免费', '国家专项', '地方专项',
}
# Normalized forms
PRESERVED_SIMPLE_LOWER = {s.lower() for s in PRESERVED_SIMPLE}

# ============================================================
# TUITION / DURATION extraction patterns
# ============================================================
TUITION_RE = re.compile(r'(\d{3,6})\s*元/\s*[年每学]')
DURATION_RE = re.compile(r'学制\s*(\d+|[一二三四五六七八九十]+)\s*年?')

def normalize_paren(s):
    """Normalize parentheses: convert half-width to full-width, collapse double parens."""
    # First, convert all half-width to full-width for consistency
    s = s.replace('(', '（').replace(')', '）')
    # Collapse double parens: （（xxx）） → （xxx）
    # This handles: （（师范））, （（学制5年））, etc.
    while '（（' in s and '））' in s:
        s = re.sub(r'（（([^（）]*?)））', r'（\1）', s)
    return s

def extract_clean_major(raw_major):
    """
    Process a single major string.
    Returns (cleaned_major, direction, extracted_tuition, extracted_duration).
    
    - cleaned_major: major name with junk removed but preserved modifiers kept
    - direction: extracted direction info (e.g. "新能源发电方向")
    - extracted_tuition: integer tuition value if found, else None
    - extracted_duration: string duration if found (e.g. "5"), else None
    """
    if not raw_major or not isinstance(raw_major, str):
        return raw_major, None, None, None
    
    major = raw_major.strip()
    original = major
    
    # Step 0: Normalize parentheses
    major = normalize_paren(major)
    
    extracted_tuition = None
    extracted_duration = None
    direction = None
    
    # Step 1: Find and catalog all parenthesized segments
    paren_segments = []
    
    def find_parens(s):
        """Find all (innermost first) parenthesized segments. Returns list of (start, end, content)."""
        results = []
        stack = []
        for i, ch in enumerate(s):
            if ch in '（(':
                stack.append(i)
            elif ch in '）)':
                if stack:
                    start = stack.pop()
                    content = s[start+1:i]
                    results.append((start, i, content))
        # Sort by length (innermost first)
        results.sort(key=lambda x: x[1] - x[0])
        return results
    
    parens = find_parens(major)
    
    if not parens:
        return major, None, None, None
    
    # For each paren segment, classify: preserved, tuition, duration, or junk
    to_remove = set()  # indices of parens to remove
    directions = []
    
    for start, end, content in parens:
        content_stripped = content.strip()
        
        # Check if this is a preserved modifier
        content_lower = content_stripped.lower()
        is_preserved = False
        for preserved in PRESERVED_SIMPLE_LOWER:
            if preserved in content_lower and len(content_lower) <= len(preserved) + 10:
                # Also check: is this paren the full match or just part of a longer one?
                # For preserved items like "师范", "中外合作办学", check if the content is mostly just this
                # This handles cases like "（师范）", "（中外合作办学）", etc.
                if content_lower == preserved or content_lower.startswith(preserved):
                    is_preserved = True
                    break
                # Also handle cases like "（）师范" or "师范）"
        
        if is_preserved:
            continue  # Keep it
        
        # Try to extract tuition
        tuition_match = TUITION_RE.search(content_stripped)
        if tuition_match:
            extracted_tuition = int(tuition_match.group(1))
            to_remove.add((start, end))
            
            # After removing tuition, check if remaining content has a direction
            remaining = TUITION_RE.sub('', content_stripped).strip('；;，, ')
            if remaining and len(remaining) > 1:
                # Check if remaining is a direction-like phrase
                if any(kw in remaining for kw in ['方向', '培养', '教学', '校区', '地点']):
                    continue  # It's junk, already marked for removal
                else:
                    directions.append(remaining)
            continue
        
        # Try to extract duration
        duration_match = DURATION_RE.search(content_stripped)
        if duration_match:
            dur_str = duration_match.group(1)
            # Convert Chinese numerals to digits
            cn_nums = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
                       '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'}
            if dur_str in cn_nums:
                dur_str = cn_nums[dur_str]
            extracted_duration = dur_str
            to_remove.add((start, end))
            continue
        
        # Check for direction keywords
        direction_kw = re.search(r'(.+?)(方向|特色|模块)$', content_stripped)
        if direction_kw:
            directions.append(content_stripped)
            to_remove.add((start, end))
            continue
        
        # Check for junk keywords
        junk_kws = [
            '办学地点', '只招', '不招', '学费', '元/年', '元/学年',
            '培养模式', '收费标准', '招生章程', '咨询院校', '单列专业',
            '应用科技学院', '软件类', '特殊培养', '嵌入式培养',
            '少数民族', '只招少数民族', '男生', '女生',
            '全科教师', '免费全科', '国家免费', '免费医学',
            '联合培养', '双语班', '中外课程合作', '国家级一流',
            '马来西亚', '厦门大学马来西亚',
            '5+3', '5+3一体化', '学制八年', '学制五年', '学制两年',
            '注册会计师', '管理会计', '跨境电商', '注册师',
            '北京', '只招英语', '色盲', '色弱',
        ]
        
        is_junk = False
        for kw in junk_kws:
            if kw in content_stripped:
                is_junk = True
                break
        
        if is_junk:
            to_remove.add((start, end))
            continue
        
        # If we reach here and content looks like a direction (not junk, not preserved)
        # e.g. "新能源发电方向", "自贸区贸易管理与服务"
        # Also handle cases like "（2）" which just means nothing useful
        if re.match(r'^\d+$', content_stripped):
            to_remove.add((start, end))
            continue
        
        # If content is short and not a known preserved item, treat as direction
        if len(content_stripped) <= 30:
            directions.append(content_stripped)
            to_remove.add((start, end))
        else:
            # Long content - probably junk descriptions
            to_remove.add((start, end))
    
    # Step 2: Remove junk parenthesized segments from the major string
    # Build the cleaned string
    result_chars = []
    i = 0
    removal_spans = sorted(to_remove)
    span_idx = 0
    
    while i < len(major):
        if span_idx < len(removal_spans) and i == removal_spans[span_idx][0]:
            # Skip this entire parenthesized segment
            i = removal_spans[span_idx][1] + 1
            span_idx += 1
        else:
            result_chars.append(major[i])
            i += 1
    
    cleaned = ''.join(result_chars)
    
    # Clean up artifacts
    cleaned = re.sub(r'（\s*）', '', cleaned)  # Empty parens
    cleaned = re.sub(r'\s+', '', cleaned)  # Collapse whitespace
    cleaned = cleaned.strip()
    
    # If no meaningful content remains, return original
    if not cleaned:
        cleaned = raw_major
    
    # Consolidate directions
    if directions:
        direction = '；'.join(directions)
    
    return cleaned, direction, extracted_tuition, extracted_duration


def make_key(record):
    """Create a merge key for deduplication."""
    return (
        record.get('year'),
        record.get('school', ''),
        record.get('school_code', ''),
        record.get('major_code', ''),
        record.get('major', ''),  # cleaned major name
    )


def main():
    print("=" * 60)
    print("Admission Plans Major Field Cleaner")
    print("=" * 60)
    
    # Load data
    print(f"\n[1/5] Loading data from {INPUT}...")
    with open(INPUT, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    
    records = raw['data']
    meta = raw['meta']
    total_before = len(records)
    print(f"  Loaded {total_before:,} records")
    
    # --- PASS 1: Clean major fields ---
    print(f"\n[2/5] Cleaning major fields...")
    
    parens_cleaned = 0
    tuition_extracted = 0
    direction_extracted = 0
    cleaned_records = []
    
    for i, rec in enumerate(records):
        major = rec.get('major', '')
        cleaned, direction, tuition_val, duration_val = extract_clean_major(major)
        
        if cleaned != major:
            parens_cleaned += 1
        
        new_rec = dict(rec)
        new_rec['major'] = cleaned
        
        if direction:
            new_rec['direction'] = direction
            direction_extracted += 1
        
        if tuition_val is not None:
            existing_tuition = rec.get('tuition')
            if existing_tuition is None or existing_tuition == '' or existing_tuition == 0:
                new_rec['tuition'] = tuition_val
                tuition_extracted += 1
        
        if duration_val is not None:
            existing_duration = rec.get('duration', '')
            if existing_duration in (None, '', '-', '0'):
                new_rec['duration'] = duration_val
        
        cleaned_records.append(new_rec)
        
        if (i + 1) % 100000 == 0:
            print(f"  Processed {i+1:,} / {total_before:,} records...")
    
    print(f"  Done. {parens_cleaned:,} majors cleaned, {tuition_extracted:,} tuitions extracted, {direction_extracted:,} directions extracted")
    
    # --- PASS 2: Merge duplicates ---
    print(f"\n[3/5] Merging duplicates...")
    print(f"  Records before merge: {len(cleaned_records):,}")
    
    # Group by (year, school, school_code, major_code, major)
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
            # Merge: sum planned_count, take first for other fields
            merged = dict(group[0])
            total_planned = sum(r.get('planned_count', 0) for r in group)
            merged['planned_count'] = total_planned
            merged_records.append(merged)
            duplicates_removed += len(group) - 1
    
    total_after = len(merged_records)
    print(f"  Records after merge: {total_after:,}")
    print(f"  Duplicates removed: {duplicates_removed:,}")
    
    # --- PASS 3: Validate ---
    print(f"\n[4/5] Validating results...")
    # Show some examples of cleaned majors
    cleaned_examples = []
    for rec in records:
        major = rec.get('major', '')
        cleaned, direction, _, _ = extract_clean_major(major)
        if cleaned != major:
            cleaned_examples.append((major, cleaned, direction))
        if len(cleaned_examples) >= 20:
            break
    
    print("  Example transformations:")
    for orig, new, direction in cleaned_examples:
        print(f"    [{orig}] → [{new}]" + (f"  dir=[{direction}]" if direction else ""))
    
    # --- SAVE ---
    print(f"\n[5/5] Saving results...")
    
    output_data = {
        'meta': {
            **meta,
            'cleaned_at': '2026-05-28 16:04:00',
            'records_before_cleaning': total_before,
            'records_after_cleaning': total_after,
            'duplicates_removed': duplicates_removed,
            'parens_cleaned': parens_cleaned,
            'tuition_extracted': tuition_extracted,
            'direction_extracted': direction_extracted,
        },
        'data': merged_records
    }
    
    print(f"  Writing cleaned data to {OUTPUT}...")
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False)
    
    # Report
    report = {
        'total_before': total_before,
        'total_after': total_after,
        'duplicates_removed': duplicates_removed,
        'parentheses_cleaned': parens_cleaned,
        'tuition_extracted': tuition_extracted,
        'direction_extracted': direction_extracted,
        'dedup_rate': f"{duplicates_removed/total_before*100:.2f}%",
        'clean_rate': f"{parens_cleaned/total_before*100:.2f}%",
    }
    
    print(f"  Writing report to {REPORT}...")
    with open(REPORT, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # --- SUMMARY ---
    import os
    output_size = os.path.getsize(OUTPUT)
    
    print("\n" + "=" * 60)
    print("CLEANUP SUMMARY")
    print("=" * 60)
    print(f"  Total records before:  {total_before:>10,}")
    print(f"  Total records after:   {total_after:>10,}")
    print(f"  Duplicates removed:    {duplicates_removed:>10,}")
    print(f"  Parentheses cleaned:   {parens_cleaned:>10,}")
    print(f"  Tuitions extracted:    {tuition_extracted:>10,}")
    print(f"  Directions extracted:  {direction_extracted:>10,}")
    print(f"  Output size:           {output_size/1024/1024:>10.1f} MB")
    print(f"  Output: {OUTPUT}")
    print(f"  Report: {REPORT}")
    print("=" * 60)


if __name__ == '__main__':
    main()
