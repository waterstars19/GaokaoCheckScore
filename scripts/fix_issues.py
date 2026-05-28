#!/usr/bin/env python3
"""Fix remaining issues in admission_plans_cleaned.json"""

import json
import re
import os
from collections import defaultdict

CLEANED = r"D:\GoakaoProject\docs\admission_plans_cleaned.json"
ORIGINAL = r"D:\GoakaoProject\docs\admission_plans.json"
REPORT = r"D:\GoakaoProject\docs\admission_plans_cleanup_report.json"

# Reserved words that should stay in major name
RESERVED = [
    "中外合作办学", "师范", "师范类", "实验班", "卓越班",
    "基地班", "创新班", "民族班", "定向", "免费",
    "国家专项", "地方专项"
]

# Patterns to remove from major (campus/location info)
CAMPUS_PATTERNS = [
    re.compile(r'办学地点.*$'),
    re.compile(r'办学地点为.*$'),
    re.compile(r'就读地点.*$'),
    re.compile(r'教学地点.*$'),
    re.compile(r'培养模式.*$'),
    re.compile(r'收费标准.*$'),
    re.compile(r'收费方式.*$'),
]

def fix_double_brackets(major):
    """Fix double-bracket patterns like （（xxx）） or ((xxx))"""
    original = major
    # Match full-width double brackets: （（...））
    # Also handle triple brackets
    # Pattern: content before double bracket, then （（inner）） 
    # e.g., "汽车制造类（中外合作办学）（（汽车检测与维修技术））"
    #        "应用化学（（核科学与技术基地班））"
    #        "机械类（中外合作办学）（（工业设计））"
    
    # Full-width patterns
    while True:
        # Match （（inner）） 
        m = re.search(r'（（([^）]+?)））', major)
        if not m:
            # Match ((inner))
            m = re.search(r'\(\(([^)]+?)\)\)', major)
        if not m:
            # Match （（（inner）））  - triple brackets
            m = re.search(r'（（（([^）]+?)）））', major)
        if not m:
            # Match (((inner))) 
            m = re.search(r'\(\(\(([^)]+?)\)\)\)', major)
        if not m:
            break
        
        inner = m.group(1).strip()
        # Check if inner contains any reserved word
        is_reserved = any(rw in inner for rw in RESERVED)
        
        if is_reserved:
            # Keep it in major, unwrap to single brackets
            major = major[:m.start()] + '（' + inner + '）' + major[m.end():]
        else:
            # Move to direction (just remove from major for now)
            major = major[:m.start()] + major[m.end():]
            # We'll set direction separately
    
    # Clean up stray parentheses
    major = major.strip()
    # Remove trailing/leading spaces from parens
    major = re.sub(r'\(\s+', '(', major)
    major = re.sub(r'\s+\)', ')', major)
    major = re.sub(r'（\s+', '（', major)
    major = re.sub(r'\s+）', '）', major)
    
    return major, (major != original)


def extract_direction_from_brackets(major):
    """Extract the direction from double-bracket content that should be moved"""
    # Full-width patterns
    m = re.search(r'（（([^）]+?)））', major)
    if not m:
        m = re.search(r'\(\(([^)]+?)\)\)', major)
    if not m:
        m = re.search(r'（（（([^）]+?)）））', major)
    if not m:
        m = re.search(r'\(\(\(([^)]+?)\)\)\)', major)
    if not m:
        return None
    
    inner = m.group(1).strip()
    is_reserved = any(rw in inner for rw in RESERVED)
    if is_reserved:
        return None
    return inner


def fix_campus_location(major):
    """Remove campus/location info from major name"""
    original = major
    for pat in CAMPUS_PATTERNS:
        major = pat.sub('', major)
    major = major.strip()
    # Remove trailing punctuation
    major = major.rstrip('，,；;：:。.、')
    return major, (major != original)


def main():
    print("Loading cleaned data...")
    with open(CLEANED, 'r', encoding='utf-8') as f:
        d = json.load(f)
    
    data = d['data']
    total = len(data)
    print(f"Total records: {total}")
    
    stats = {
        "double_brackets_fixed": 0,
        "double_brackets_kept_in_major": 0,
        "double_brackets_moved_to_direction": 0,
        "campus_location_removed": 0,
        "empty_majors_fixed": 0,
        "empty_majors_marked_unknown": 0,
    }
    
    # ==========================================
    # Issue 1: Double brackets
    # ==========================================
    print("\n=== Fixing double brackets ===")
    double_fixed = 0
    double_kept = 0
    double_moved = 0
    
    for i, rec in enumerate(data):
        major = rec.get('major', '')
        if not major:
            continue
        
        has_double = "((" in major or chr(65288)*2 in major
        if not has_double:
            continue
        
        # Get direction before fixing
        direction = extract_direction_from_brackets(major)
        
        # Fix the major
        new_major, changed = fix_double_brackets(major)
        
        if changed:
            double_fixed += 1
            rec['major'] = new_major
            
            if direction:
                # Check if reserved
                is_reserved = any(rw in direction for rw in RESERVED)
                if is_reserved:
                    double_kept += 1
                    # Already handled - unwrapped to single brackets
                else:
                    double_moved += 1
                    # Set direction if not already set
                    existing_dir = rec.get('direction', '')
                    if not existing_dir:
                        rec['direction'] = direction
                    elif direction not in existing_dir:
                        rec['direction'] = existing_dir + '; ' + direction
            else:
                double_kept += 1
    
    stats['double_brackets_fixed'] = double_fixed
    stats['double_brackets_kept_in_major'] = double_kept
    stats['double_brackets_moved_to_direction'] = double_moved
    print(f"  Fixed: {double_fixed} (kept in major: {double_kept}, moved to direction: {double_moved})")
    
    # ==========================================
    # Issue 2: Campus location in major
    # ==========================================
    print("\n=== Fixing campus/location info in major ===")
    campus_fixed = 0
    for rec in data:
        major = rec.get('major', '')
        if not major:
            continue
        
        new_major, changed = fix_campus_location(major)
        if changed:
            campus_fixed += 1
            rec['major'] = new_major
    
    stats['campus_location_removed'] = campus_fixed
    print(f"  Fixed: {campus_fixed}")
    
    # ==========================================
    # Issue 3: Empty majors
    # ==========================================
    print("\n=== Fixing empty majors ===")
    
    # First, let's find all empty majors
    empty_indices = [i for i, rec in enumerate(data) if not rec.get('major', '').strip()]
    print(f"  Empty majors: {len(empty_indices)}")
    
    if empty_indices:
        # Load original data
        print("  Loading original data for cross-referencing...")
        with open(ORIGINAL, 'r', encoding='utf-8') as f:
            orig = json.load(f)
        orig_data = orig.get('data', [])
        print(f"  Original records: {len(orig_data)}")
        
        # Build lookup from original: key = (school, year, province, batch, planned_count)
        # We'll use this to find original major names
        orig_lookup = defaultdict(list)
        for r in orig_data:
            key = (r.get('school', ''), r.get('year', 0), r.get('province', ''), 
                   r.get('batch', ''), r.get('planned_count', 0))
            m = r.get('major', '')
            if m and m.strip():
                # Also store by school_code as backup
                key2 = (r.get('school_code', ''), r.get('year', 0), r.get('province', ''),
                        r.get('batch', ''), r.get('planned_count', 0))
                orig_lookup[key].append(m)
                if key2 != key:
                    orig_lookup[key2].append(m)
        
        fixed_count = 0
        unknown_count = 0
        
        for idx in empty_indices:
            rec = data[idx]
            key = (rec.get('school', ''), rec.get('year', 0), rec.get('province', ''),
                   rec.get('batch', ''), rec.get('planned_count', 0))
            key2 = (rec.get('school_code', ''), rec.get('year', 0), rec.get('province', ''),
                    rec.get('batch', ''), rec.get('planned_count', 0))
            
            candidates = orig_lookup.get(key, []) + orig_lookup.get(key2, [])
            # Also try without batch
            if not candidates:
                key_no_batch = (rec.get('school', ''), rec.get('year', 0), rec.get('province', ''),
                               '', rec.get('planned_count', 0))
                candidates = orig_lookup.get(key_no_batch, [])
            if not candidates:
                key_no_batch2 = (rec.get('school_code', ''), rec.get('year', 0), rec.get('province', ''),
                                '', rec.get('planned_count', 0))
                candidates = orig_lookup.get(key_no_batch2, [])
            
            if candidates:
                # Use most common candidate
                from collections import Counter
                most_common = Counter(candidates).most_common(1)[0][0]
                rec['major'] = most_common
                fixed_count += 1
            else:
                rec['major'] = '未知专业'
                unknown_count += 1
        
        stats['empty_majors_fixed'] = fixed_count
        stats['empty_majors_marked_unknown'] = unknown_count
        print(f"  Restored from original: {fixed_count}")
        print(f"  Marked as unknown: {unknown_count}")
    
    # ==========================================
    # Post-checks
    # ==========================================
    print("\n=== Post-check ===")
    
    # Check remaining double brackets
    remaining = sum(1 for r in data if "((" in r.get('major','') or chr(65288)*2 in r.get('major',''))
    print(f"  Remaining double brackets: {remaining}")
    
    # Check remaining campus patterns
    remaining_campus = sum(1 for r in data if re.search(r'办学地点', r.get('major','')) != None)
    print(f"  Remaining campus location in major: {remaining_campus}")
    
    # Check remaining empty majors
    remaining_empty = sum(1 for r in data if not r.get('major','').strip())
    print(f"  Remaining empty majors: {remaining_empty}")
    
    # Update meta
    d['meta']['fixes_applied'] = stats
    d['meta']['fixes_generated_at'] = "2026-05-28 16:30:00"
    
    # Save cleaned file
    print("\nSaving cleaned data...")
    with open(CLEANED, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False)
    print(f"Saved: {CLEANED}")
    
    # Update report
    report = {}
    if os.path.exists(REPORT):
        with open(REPORT, 'r', encoding='utf-8') as f:
            report = json.load(f)
    
    report['fixes_round_2'] = stats
    report['fixes_round_2_timestamp'] = "2026-05-28 16:30:00"
    
    with open(REPORT, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Saved report: {REPORT}")
    
    # Print summary
    print("\n" + "="*50)
    print("FINAL STATISTICS")
    print("="*50)
    print(f"Total records: {total}")
    print(f"Double brackets fixed: {double_fixed}")
    print(f"  - Kept in major (reserved): {double_kept}")
    print(f"  - Moved to direction: {double_moved}")
    print(f"Campus location cleaned: {campus_fixed}")
    print(f"Empty majors:")
    print(f"  - Restored from original: {stats['empty_majors_fixed']}")
    print(f"  - Marked unknown: {stats['empty_majors_marked_unknown']}")
    print(f"Remaining issues: {remaining} double brackets, {remaining_campus} campus, {remaining_empty} empty")
    print("="*50)


if __name__ == '__main__':
    main()
