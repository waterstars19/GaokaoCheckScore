#!/usr/bin/env python3
"""Fix remaining issues in admission_plans_cleaned.json - Round 2"""

import json
import re
import os
from collections import defaultdict, Counter

CLEANED = r"D:\GoakaoProject\docs\admission_plans_cleaned.json"
ORIGINAL = r"D:\GoakaoProject\docs\admission_plans.json"
REPORT = r"D:\GoakaoProject\docs\admission_plans_cleanup_report.json"

# Reserved words that should stay in major name
RESERVED = [
    "中外合作办学", "师范", "师范类", "实验班", "卓越班",
    "基地班", "创新班", "民族班", "定向", "免费",
    "国家专项", "地方专项",
    # Additional attributes that describe the program type
    "五年制", "八年制", "四年制", "三年制",
    "英才班", "非师范", "国家理科基地班",
    # Common suffixes
    "卓越计划", "卓越医生教育培养计划",
]

CAMPUS_REMOVE_RE = re.compile(r'办学地点[为：:\s]*[^\s；;，,）)]*(?:[；;，,）)]|$)')
LOCATION_REMOVE_RE = re.compile(r'就读地点[为：:\s]*[^\s；;，,）)]*(?:[；;，,）)]|$)')

def find_matching_close(s, open_pos, open_chr, close_chr):
    """Find matching closing bracket, accounting for nesting"""
    depth = 0
    for i in range(open_pos, len(s)):
        if s[i] == open_chr:
            depth += 1
        elif s[i] == close_chr:
            depth -= 1
            if depth == 0:
                return i
    return -1

def fix_double_brackets_v2(major):
    """
    Handle all double bracket patterns more comprehensively.
    Returns (new_major, extracted_for_direction, changed)
    """
    original = major
    extracted_parts = []
    
    # First try standard nested pattern: （（inner）） or ((inner))
    while True:
        made_change = False
        
        # Pattern 1: Standard （（...）） with balanced parens
        pos = major.find(chr(65288)*2)  # （（
        if pos < 0:
            pos = major.find("((")
        if pos < 0:
            break
        
        open_chr = major[pos]
        close_chr = chr(65289) if open_chr == chr(65288) else ')'
        
        # Find the end of the content region
        # The inner content starts at pos+2
        inner_start = pos + 2
        
        # Try to find the matching closing brackets
        # First find inner close
        inner_close = find_matching_close(major, inner_start, open_chr, close_chr)
        
        if inner_close >= 0:
            # Check if there's also outer close
            if inner_close + 1 < len(major) and major[inner_close + 1] == close_chr:
                # Full balanced pattern: （（inner）） 
                inner = major[inner_start:inner_close].strip()
                outer_end = inner_close + 2
                
                # Check for additional content after ）） like 、xxx
                rest_start = outer_end
                rest = ""
                if rest_start < len(major) and major[rest_start] in ('、', '，', ',', ';', '；', '）', ')'):
                    # There's more content appended after the double bracket
                    # e.g., （（实验班）、经济统计学）
                    rest = major[rest_start:].lstrip('）、)、，,、;；')
                    outer_end = len(major)  # remove everything from ）） onwards
            else:
                # Only inner close found, outer might be missing
                # This is （（inner） but no outer ） - check if it's actually （（inner）
                inner = major[inner_start:inner_close].strip()
                rest = major[inner_close+1:].lstrip('）、)、，,、;；')
                outer_end = len(major)
        else:
            # Can't find even inner close - unbalanced, truncate from （（
            inner = major[inner_start:].strip()
            rest = ""
            outer_end = len(major)
        
        # Check if inner contains reserved words
        is_reserved = any(rw in inner for rw in RESERVED)
        
        if is_reserved:
            # Unwrap: XX（（inner+rest）→ XX（inner） and direction=rest
            major = major[:pos].rstrip() + open_chr + inner + close_chr
            if rest:
                extracted_parts.append(rest)
        else:
            # Move both inner and rest to direction
            major = major[:pos].rstrip()
            if inner:
                extracted_parts.append(inner)
            if rest:
                extracted_parts.append(rest)
        
        made_change = True
    
    # Clean up
    major = major.strip()
    major = re.sub(r'(\s*[\(\（]\s*)', lambda m: m.group(0).strip(), major)
    major = re.sub(r'(\s*[\)\）]\s*)', lambda m: m.group(0).strip(), major)
    major = major.rstrip('，,;；:：.')
    
    return major, '; '.join(filter(None, extracted_parts)), (major != original)


def fix_campus_location_v2(major):
    """Remove all campus/location info from major, handling complex patterns"""
    original = major
    
    # Pattern 1: Remove standalone campus info (already done in v1)
    # Pattern 2: Remove campus info inside semicolon-separated parts
    # e.g., "临床医学（本博连读）（6500元/年；办学地点医学院；国家一流本科...）"
    
    # Split on ；or ; and filter out parts containing 办学地点/就读地点
    for sep in ['；', ';']:
        if sep not in major:
            continue
        # Find and remove segments containing campus info
        parts = major.split(sep)
        filtered = []
        for part in parts:
            if re.search(r'办学地点|就读地点|教学地点|培养模式|收费标准', part):
                continue
            filtered.append(part)
        major = sep.join(filtered)
    
    # Remove standalone campus location patterns
    major = CAMPUS_REMOVE_RE.sub('', major)
    major = LOCATION_REMOVE_RE.sub('', major)
    
    # Also handle: name办学地点xxx format (no separator)
    major = re.sub(r'办学地点[为]?[^\s；;，,）)\]]*', '', major)
    major = re.sub(r'就读地点[为]?[^\s；;，,）)\]]*', '', major)
    major = re.sub(r'教学地点[为]?[^\s；;，,）)\]]*', '', major)
    
    # Clean up
    major = re.sub(r'；+', '；', major)
    major = re.sub(r';;+', ';', major)
    major = re.sub(r'（\s*）', '', major)  # Empty parens
    major = re.sub(r'\(\s*\)', '', major)
    major = major.strip()
    major = major.rstrip('，,;；:：.')
    
    return major, (major != original)


def main():
    print("Loading cleaned data...")
    with open(CLEANED, 'r', encoding='utf-8') as f:
        d = json.load(f)
    
    data = d['data']
    total = len(data)
    print(f"Total records: {total}")
    
    stats = {
        "round2_double_brackets_fixed": 0,
        "round2_double_kept": 0,
        "round2_double_moved": 0,
        "round2_campus_removed": 0,
        "round2_empty_fixed": 0,
        "round2_empty_unknown": 0,
    }
    
    # ==========================================
    # Pass 1: Double brackets v2
    # ==========================================
    print("\n=== Pass 1: Double brackets v2 ===")
    db_fixed = 0
    db_kept = 0
    db_moved = 0
    
    for i, rec in enumerate(data):
        major = rec.get('major', '')
        if not major:
            continue
        
        has_double = "((" in major or chr(65288)*2 in major
        if not has_double:
            continue
        
        new_major, extracted, changed = fix_double_brackets_v2(major)
        
        if changed:
            db_fixed += 1
            rec['major'] = new_major
            
            if extracted:
                # Check if extracted content has reserved words
                is_reserved = any(rw in extracted for rw in RESERVED)
                if is_reserved:
                    db_kept += 1
                else:
                    db_moved += 1
                    existing_dir = rec.get('direction', '')
                    if not existing_dir:
                        rec['direction'] = extracted
                    elif extracted not in existing_dir:
                        rec['direction'] = existing_dir + '; ' + extracted
    
    stats['round2_double_brackets_fixed'] = db_fixed
    stats['round2_double_kept'] = db_kept
    stats['round2_double_moved'] = db_moved
    print(f"  Fixed: {db_fixed} (kept: {db_kept}, moved to direction: {db_moved})")
    
    # Check remaining
    remaining_db = sum(1 for r in data if "((" in r.get('major','') or chr(65288)*2 in r.get('major',''))
    print(f"  Remaining: {remaining_db}")
    if remaining_db > 0:
        print("  Sample remaining:")
        for i, r in enumerate(data):
            m = r.get('major','')
            if "((" in m or chr(65288)*2 in m:
                remaining_db -= 1
                print(f"    [{i}] {repr(m[:200])}")
                if remaining_db <= 0:
                    break
    
    # ==========================================
    # Pass 2: Campus location v2
    # ==========================================
    print("\n=== Pass 2: Campus location v2 ===")
    campus_fixed = 0
    for rec in data:
        major = rec.get('major', '')
        if not major:
            continue
        
        has_campus = '办学地点' in major or '就读地点' in major or '教学地点' in major
        if not has_campus:
            continue
        
        new_major, changed = fix_campus_location_v2(major)
        if changed:
            campus_fixed += 1
            rec['major'] = new_major
    
    stats['round2_campus_removed'] = campus_fixed
    print(f"  Fixed: {campus_fixed}")
    
    remaining_cp = sum(1 for r in data if '办学地点' in r.get('major','') or '就读地点' in r.get('major',''))
    print(f"  Remaining: {remaining_cp}")
    if remaining_cp > 0:
        print("  Sample remaining:")
        for i, r in enumerate(data):
            m = r.get('major','')
            if '办学地点' in m or '就读地点' in m:
                remaining_cp -= 1
                print(f"    [{i}] {repr(m[:200])}")
                if remaining_cp <= 0:
                    break
    
    # ==========================================
    # Pass 3: Empty majors - improved matching
    # ==========================================
    print("\n=== Pass 3: Empty majors - improved matching ===")
    
    empty_indices = [i for i, rec in enumerate(data) if not rec.get('major', '').strip()]
    print(f"  Empty majors: {len(empty_indices)}")
    
    if empty_indices:
        print("  Loading original data for cross-referencing...")
        with open(ORIGINAL, 'r', encoding='utf-8') as f:
            orig = json.load(f)
        orig_data = orig.get('data', [])
        print(f"  Original records: {len(orig_data)}")
        
        # Build multiple lookup strategies
        # Strategy 1: exact match by key
        orig_lookup = defaultdict(list)
        for r in orig_data:
            m = r.get('major', '')
            if not m or not m.strip():
                continue
            # Key by school + year + province
            k1 = (r.get('school', ''), str(r.get('year', '')), r.get('province', ''))
            orig_lookup[k1].append(m)
            # Key by school_code + year + province
            k2 = (r.get('school_code', ''), str(r.get('year', '')), r.get('province', ''))
            if k2 != k1:
                orig_lookup[k2].append(m)
            # Key by school + year only
            k3 = (r.get('school', ''), str(r.get('year', '')))
            orig_lookup[k3].append(m)
        
        fixed_count = 0
        unknown_count = 0
        
        for idx in empty_indices:
            rec = data[idx]
            school = rec.get('school', '')
            school_code = rec.get('school_code', '')
            year = str(rec.get('year', ''))
            province = rec.get('province', '')
            
            candidates = []
            
            # Try various lookup keys
            keys = [
                (school, year, province),
                (school_code, year, province),
                (school, year),
                (school_code, year),
            ]
            
            for k in keys:
                if k in orig_lookup:
                    candidates.extend(orig_lookup[k])
                    if candidates:
                        break
            
            if candidates:
                most_common = Counter(candidates).most_common(1)[0][0]
                rec['major'] = most_common
                fixed_count += 1
            else:
                rec['major'] = '未知专业'
                unknown_count += 1
        
        stats['round2_empty_fixed'] = fixed_count
        stats['round2_empty_unknown'] = unknown_count
        print(f"  Restored from original: {fixed_count}")
        print(f"  Marked as unknown: {unknown_count}")
    
    # ==========================================
    # Final checks
    # ==========================================
    print("\n=== Final checks ===")
    r1 = sum(1 for r in data if "((" in r.get('major','') or chr(65288)*2 in r.get('major',''))
    r2 = sum(1 for r in data if '办学地点' in r.get('major','') or '就读地点' in r.get('major',''))
    r3 = sum(1 for r in data if not r.get('major','').strip())
    print(f"  Double brackets: {r1}")
    print(f"  Campus in major: {r2}")
    print(f"  Empty majors: {r3}")
    
    # Update meta
    d['meta']['fixes_round2'] = stats
    d['meta']['fixes_round2_generated_at'] = "2026-05-28 16:45:00"
    
    # Save
    print("\nSaving...")
    with open(CLEANED, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False)
    print(f"Saved: {CLEANED}")
    
    # Update report
    report = {}
    if os.path.exists(REPORT):
        with open(REPORT, 'r', encoding='utf-8') as f:
            report = json.load(f)
    
    all_fixes = report.get('fixes_round_2', report.get('fixes_applied', {}))
    all_fixes.update(stats)
    report['fixes_round_2'] = all_fixes
    report['fixes_round_2_timestamp'] = "2026-05-28 16:45:00"
    
    with open(REPORT, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*60)
    print("FINAL STATISTICS (Round 2)")
    print("="*60)
    print(f"Total records: {total}")
    print(f"Double brackets fixed: {db_fixed}")
    print(f"  - Kept in major (reserved): {db_kept}")
    print(f"  - Moved to direction: {db_moved}")
    print(f"Campus location cleaned: {campus_fixed}")
    print(f"Empty majors: fixed={fixed_count if empty_indices else 0}, unknown={unknown_count if empty_indices else 0}")
    print(f"Remaining: {r1} double brackets, {r2} campus, {r3} empty")
    print("="*60)


if __name__ == '__main__':
    main()
