#!/usr/bin/env python3
"""Fix remaining issues in admission_plans_cleaned.json - Round 3 (Quality Fix)"""

import json
import re
import os

CLEANED = r"D:\GoakaoProject\docs\admission_plans_cleaned.json"
REPORT = r"D:\GoakaoProject\docs\admission_plans_cleanup_report.json"

RESERVED = [
    "中外合作办学", "师范", "师范类", "实验班", "卓越班",
    "基地班", "创新班", "民族班", "定向", "免费",
    "国家专项", "地方专项",
    "五年制", "八年制", "四年制", "三年制",
    "英才班", "非师范", "国家理科基地班",
    "卓越计划", "卓越医生教育培养计划",
]

def clean_trailing_brackets(text):
    """Remove stray trailing brackets/punctuation"""
    text = text.strip()
    # Remove trailing ）) that are unmatched
    while text.endswith(chr(65289)) or text.endswith(')'):
        text = text[:-1].strip()
    text = text.rstrip('，,;；:：、.')
    return text


def fix_major_double_brackets(major):
    """
    Comprehensive fix for double-bracket patterns.
    Returns (cleaned_major, direction_to_add, changed)
    """
    # Already clean?
    if "((" not in major and chr(65288)*2 not in major:
        return major, None, False
    
    original = major
    direction_parts = []
    
    # Keep processing until no more double brackets
    max_iter = 10
    for _ in range(max_iter):
        # Find first （（ or ((
        ff_pos = major.find(chr(65288)*2)
        if ff_pos < 0:
            ff_pos = major.find("((")
        if ff_pos < 0:
            break
        
        open_ch = major[ff_pos]
        close_ch = chr(65289) if open_ch == chr(65288) else ')'
        
        # Content of what was before the double bracket
        prefix = major[:ff_pos].rstrip()
        
        # Everything from （（ onwards
        rest = major[ff_pos + 2:]
        
        # Find the first ） or ) in rest (inner close)
        inner_close_pos = rest.find(close_ch)
        if inner_close_pos < 0:
            # No close at all - just remove from （（ onwards
            major = prefix
            direction_parts.append(rest)
            continue
        
        inner = rest[:inner_close_pos]
        after_inner_close = rest[inner_close_pos + 1:]
        
        # Check if there's a second closing bracket
        if after_inner_close.startswith(close_ch):
            # Pattern: （（inner））
            after_outer = after_inner_close[1:]
            
            # Check if inner is a reserved word
            is_reserved = any(rw in inner for rw in RESERVED)
            
            if is_reserved:
                # Keep: XX（（inner）） → XX（inner）
                major = prefix + open_ch + inner + close_ch + after_outer
            else:
                # Move to direction
                major = prefix + after_outer
                direction_parts.append(inner)
        elif after_inner_close.startswith(('、', '，', ',')):
            # Pattern: （（inner）、more） or （（inner）、more
            # Find the next ） that closes the outer
            more_start = after_inner_close.lstrip('、，,')
            outer_close_pos = -1
            
            # Scan through for the matching outer close
            depth = 0
            for i, ch in enumerate(more_start):
                if ch == open_ch:
                    depth += 1
                elif ch == close_ch:
                    if depth == 0:
                        outer_close_pos = i
                        break
                    depth -= 1
            
            if outer_close_pos >= 0:
                more = more_start[:outer_close_pos]
                after = more_start[outer_close_pos + 1:]
            else:
                more = more_start
                after = ""
            
            # Check if inner is reserved
            is_reserved = any(rw in inner for rw in RESERVED)
            
            if is_reserved:
                major = prefix + open_ch + inner + close_ch + after
                direction_parts.append(more)
            else:
                major = prefix + after
                direction_parts.append(inner)
                if more:
                    direction_parts.append(more)
        else:
            # （（inner but no second ） right after and no 、 separator
            # Just remove from （（ and put inner in direction
            major = prefix + after_inner_close
            direction_parts.append(inner)
        
        major = major.strip()
    
    # Clean up remaining stray brackets
    major = clean_trailing_brackets(major)
    major = re.sub(r'（\s*）', '', major)
    major = re.sub(r'\(\s*\)', '', major)
    
    direction = '; '.join(filter(None, direction_parts)) if direction_parts else None
    direction = clean_trailing_brackets(direction) if direction else None
    
    return major, direction, (major != original)


def fix_campus_in_major(major):
    """Remove campus location info while preserving structure"""
    original = major
    
    # Remove segments between ；separators that contain campus keywords
    campus_keywords = ['办学地点', '就读地点', '教学地点', '培养模式', '收费标准']
    
    # Pattern 1: Semicolon-separated campus segments within parentheses
    # E.g., （6500元/年；办学地点医学院；国家一流本科）
    for sep in ['；', ';']:
        if sep not in major:
            continue
        parts = major.split(sep)
        new_parts = []
        for part in parts:
            if any(kw in part for kw in campus_keywords):
                continue
            new_parts.append(part)
        major = sep.join(new_parts)
    
    # Pattern 2: Direct attachment: name办学地点xxx
    for kw in campus_keywords:
        # Remove 办学地点xxx pattern (with optional 为/：/:/space)
        major = re.sub(r'' + re.escape(kw) + r'[为：:\s]*[^\s；;，,）\)\[\]]*', '', major)
    
    # Pattern 3: Remove empty or broken parentheticals
    major = re.sub(r'（\s*[;；]\s*）', '', major)
    major = re.sub(r'\(\s*[;；]\s*\)', '', major)
    major = re.sub(r'（\s*）+', '', major)
    major = re.sub(r'\(\s*\)+', '', major)
    
    # Pattern 4: Fix unmatched （ at the end
    # e.g., "专业（内容制作）（29800元/年" → "专业（内容制作）"
    # Count all （ vs ） and if ） is missing, try to fix
    count_open = major.count('（') + major.count('(')
    count_close = major.count('）') + major.count(')')
    if count_open > count_close:
        # Remove unmatched opening parens from the end backward
        diff = count_open - count_close
        for _ in range(diff):
            # Find last unmatched opening paren
            # Work backward, tracking depth
            depth = 0
            for i in range(len(major) - 1, -1, -1):
                ch = major[i]
                if ch in ('）', ')'):
                    depth += 1
                elif ch in ('（', '('):
                    if depth == 0:
                        major = major[:i] + major[i+1:]
                        break
                    depth -= 1
    
    # Clean up
    major = major.strip()
    major = re.sub(r'；+', '；', major)
    major = re.sub(r';;+', ';', major)
    major = major.rstrip('，,;；:：、.')
    
    return major, (major != original)


def main():
    print("Loading cleaned data...")
    with open(CLEANED, 'r', encoding='utf-8') as f:
        d = json.load(f)
    
    data = d['data']
    total = len(data)
    print(f"Total records: {total}")
    
    # Count issues before
    before_db = sum(1 for r in data if "((" in r.get('major','') or chr(65288)*2 in r.get('major',''))
    before_campus = sum(1 for r in data if '办学地点' in r.get('major','') or '就读地点' in r.get('major',''))
    print(f"Before: {before_db} double brackets, {before_campus} campus in major")
    
    stats = {
        "round3_double_brackets_fixed": 0,
        "round3_direction_added": 0,
        "round3_campus_fixed": 0,
        "round3_parens_balanced": 0,
    }
    
    # ==========================================
    # Pass: Double brackets refined
    # ==========================================
    print("\n=== Fixing double brackets ===")
    db_fixed = 0
    dir_added = 0
    
    for rec in data:
        major = rec.get('major', '')
        if not major:
            continue
        if "((" not in major and chr(65288)*2 not in major:
            continue
        
        new_major, new_dir, changed = fix_major_double_brackets(major)
        if changed:
            db_fixed += 1
            rec['major'] = new_major
            
            if new_dir:
                dir_added += 1
                existing = rec.get('direction', '')
                if not existing:
                    rec['direction'] = new_dir
                elif new_dir not in existing:
                    rec['direction'] = existing + '; ' + new_dir
    
    stats['round3_double_brackets_fixed'] = db_fixed
    stats['round3_direction_added'] = dir_added
    print(f"  Fixed: {db_fixed}, directions added: {dir_added}")
    
    # Check remaining
    rem = sum(1 for r in data if "((" in r.get('major','') or chr(65288)*2 in r.get('major',''))
    print(f"  Remaining double brackets: {rem}")
    
    # ==========================================
    # Pass: Campus location refined
    # ==========================================
    print("\n=== Fixing campus location ===")
    campus_fixed = 0
    parens_fixed = 0
    
    for rec in data:
        major = rec.get('major', '')
        if not major:
            continue
        
        has_campus = any(kw in major for kw in ['办学地点', '就读地点', '教学地点'])
        has_paren_issue = major.count('（') != major.count('）') or major.count('(') != major.count(')')
        
        if has_campus or has_paren_issue:
            new_major, changed = fix_campus_in_major(major)
            if changed:
                if has_campus:
                    campus_fixed += 1
                if has_paren_issue:
                    parens_fixed += 1
                rec['major'] = new_major
    
    stats['round3_campus_fixed'] = campus_fixed
    stats['round3_parens_balanced'] = parens_fixed
    print(f"  Campus fixes: {campus_fixed}, parens balanced: {parens_fixed}")
    
    # Final checks
    print("\n=== Final checks ===")
    r1 = sum(1 for r in data if "((" in r.get('major','') or chr(65288)*2 in r.get('major',''))
    r2 = sum(1 for r in data if '办学地点' in r.get('major','') or '就读地点' in r.get('major',''))
    r3 = sum(1 for r in data if not r.get('major','').strip())
    r4 = sum(1 for r in data if r.get('major','').count('（') != r.get('major','').count('）'))
    print(f"  Double brackets: {r1}")
    print(f"  Campus in major: {r2}")
    print(f"  Empty majors: {r3}")
    print(f"  Unbalanced parens: {r4}")
    
    # Save
    d['meta']['fixes_round3'] = stats
    d['meta']['fixes_round3_generated_at'] = "2026-05-28 17:00:00"
    
    print("\nSaving...")
    with open(CLEANED, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False)
    print(f"Saved: {CLEANED}")
    
    # Update report
    report = {}
    if os.path.exists(REPORT):
        with open(REPORT, 'r', encoding='utf-8') as f:
            report = json.load(f)
    
    report['fixes_round_3'] = stats
    report['fixes_round_3_timestamp'] = "2026-05-28 17:00:00"
    
    with open(REPORT, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*60)
    print("FINAL STATISTICS (Round 3)")
    print("="*60)
    print(f"Total records: {total}")
    print(f"Double brackets fixed: {db_fixed}")
    print(f"Directions added: {dir_added}")
    print(f"Campus fixes: {campus_fixed}")
    print(f"Parens balanced: {parens_fixed}")
    print(f"Remaining: {r1} DB, {r2} campus, {r3} empty, {r4} unbalanced")
    print("="*60)


if __name__ == '__main__':
    main()
