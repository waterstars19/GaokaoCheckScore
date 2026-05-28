#!/usr/bin/env python3
"""Final cleanup pass - fix remaining parentheses issues from round 2"""
import json, re, os

CLEANED = r"D:\GoakaoProject\docs\admission_plans_cleaned.json"
REPORT = r"D:\GoakaoProject\docs\admission_plans_cleanup_report.json"

def count_parens(s):
    """Count open and close parentheses (both full-width and half-width)"""
    open_cnt = s.count(chr(65288)) + s.count('(')
    close_cnt = s.count(chr(65289)) + s.count(')')
    return open_cnt, close_cnt

def fix_unbalanced_parens(major):
    """Fix unbalanced parentheses by stripping excess close brackets"""
    original = major
    open_c, close_c = count_parens(major)
    
    while close_c > open_c:
        # Find and remove one trailing close bracket
        last_fw = major.rfind(chr(65289))  # ）
        last_hw = major.rfind(')')
        if last_fw > last_hw:
            major = major[:last_fw] + major[last_fw+1:]
        elif last_hw >= 0:
            major = major[:last_hw] + major[last_hw+1:]
        else:
            break
        open_c, close_c = count_parens(major)
    
    # Also fix: if open > close, add missing close at end
    # But this is trickier - just strip unmatched opens from end for now
    while open_c > close_c:
        last_fw = major.rfind(chr(65288))  # （
        last_hw = major.rfind('(')
        if last_fw > last_hw:
            major = major[:last_fw] + major[last_fw+1:]
        elif last_hw >= 0:
            major = major[:last_hw] + major[last_hw+1:]
        else:
            break
        open_c, close_c = count_parens(major)
    
    # Clean trailing separators
    major = major.rstrip('，,;；:：、.')
    major = major.strip()
    
    return major, (major != original)

def main():
    print("Loading cleaned data...")
    with open(CLEANED, 'r', encoding='utf-8') as f:
        d = json.load(f)
    data = d['data']
    total = len(data)
    
    # Count before
    before = sum(1 for r in data if r.get('major','') and count_parens(r['major'])[0] != count_parens(r['major'])[1])
    print(f"Records with unbalanced parens before: {before}")
    
    fixed = 0
    for rec in data:
        major = rec.get('major', '')
        if not major:
            continue
        open_c, close_c = count_parens(major)
        if open_c == close_c:
            continue
        
        new_major, changed = fix_unbalanced_parens(major)
        if changed:
            fixed += 1
            rec['major'] = new_major
    
    print(f"Fixed: {fixed}")
    
    # Check after
    after = sum(1 for r in data if r.get('major','') and count_parens(r['major'])[0] != count_parens(r['major'])[1])
    print(f"Remaining unbalanced: {after}")
    
    if after > 0:
        print("\nSample remaining:")
        count = 0
        for i, r in enumerate(data):
            m = r.get('major','')
            if not m:
                continue
            open_c, close_c = count_parens(m)
            if open_c != close_c:
                count += 1
                if count <= 15:
                    print(f'  [{i}] open={open_c} close={close_c}: {m[:150]}')
    
    # Verify double brackets
    rem_db = sum(1 for r in data if "((" in r.get('major','') or chr(65288)*2 in r.get('major',''))
    print(f"\nRemaining double brackets: {rem_db}")
    
    # Save
    d['meta']['fixes_paren_cleanup'] = {
        "unbalanced_before": before,
        "unbalanced_fixed": fixed, 
        "unbalanced_after": after,
        "generated_at": "2026-05-28 17:10:00"
    }
    
    with open(CLEANED, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False)
    print(f"\nSaved: {CLEANED}")
    
    # Update report
    report = {}
    if os.path.exists(REPORT):
        with open(REPORT, 'r', encoding='utf-8') as f:
            report = json.load(f)
    report['paren_cleanup'] = {
        "unbalanced_fixed": fixed,
        "remaining": after,
        "timestamp": "2026-05-28 17:10:00"
    }
    with open(REPORT, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
