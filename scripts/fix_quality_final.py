#!/usr/bin/env python3
"""Final quality fixes: restore corrupted majors, clean tuition from major"""
import json, re, os

CLEANED = r"D:\GoakaoProject\docs\admission_plans_cleaned.json"
ORIGINAL = r"D:\GoakaoProject\docs\admission_plans.json"
REPORT = r"D:\GoakaoProject\docs\admission_plans_cleanup_report.json"

def main():
    print("Loading cleaned data...")
    with open(CLEANED, 'r', encoding='utf-8') as f:
        d = json.load(f)
    data = d['data']
    
    # Find corrupted majors
    corrupted = []
    for i, r in enumerate(data):
        m = r.get('major','')
        if not m:
            continue
        # Corrupted if starts with non-major-name content
        if (m.startswith('国家一流') or m.startswith('合作方') or 
            m.startswith('单列专业') or m.startswith('含美国等')):
            corrupted.append(i)
    
    print("Corrupted majors to fix: {}".format(len(corrupted)))
    
    if corrupted and os.path.exists(ORIGINAL):
        print("Loading original data...")
        with open(ORIGINAL, 'r', encoding='utf-8') as f:
            orig = json.load(f)
        orig_data = orig.get('data', [])
        
        # Build lookup from original
        from collections import defaultdict, Counter
        orig_lookup = defaultdict(list)
        for r in orig_data:
            m = r.get('major','')
            if not m or not m.strip():
                continue
            k = (r.get('school',''), str(r.get('year','')), r.get('province',''), 
                 r.get('planned_count', 0))
            orig_lookup[k].append(m)
        
        restored = 0
        for idx in corrupted:
            rec = data[idx]
            k = (rec.get('school',''), str(rec.get('year','')), 
                 rec.get('province',''), rec.get('planned_count', 0))
            
            candidates = orig_lookup.get(k, [])
            if not candidates:
                k2 = (rec.get('school',''), str(rec.get('year','')), rec.get('province',''))
                candidates = orig_lookup.get(k2, [])
            
            if candidates:
                # Try to find one that contains the school name pattern
                # and filter out the broken campus info
                best = Counter(candidates).most_common(1)[0][0]
                # Clean campus info from the restored major too
                best = re.sub(r'办学地点[为：:\s]*[^\s；;，,）)\]]*', '', best)
                best = re.sub(r'就读地点[为：:\s]*[^\s；;，,）)\]]*', '', best)
                best = best.strip().rstrip('，,;；:：.')
                rec['major'] = best
                restored += 1
                print("  Restored [{}]: {} -> {}".format(idx, '...', best[:120]))
            else:
                # Fallback: just mark as unknown
                print("  Could not restore [{}]: {} at {}".format(idx, rec.get('school',''), rec.get('year')))
        
        print("Restored: {}/{}".format(restored, len(corrupted)))
    
    # Fix tuition in major
    print("\nFixing tuition info in major...")
    tuition_fixed = 0
    for rec in data:
        m = rec.get('major','')
        if not m:
            continue
        # Pattern: digits followed by 元/年 or 元/学年
        new_m = re.sub(r'\d+元/[年学][度年]?', '', m)
        new_m = re.sub(r'[（\(]\s*[;；]?\s*[）\)]', '', new_m)  # empty parens
        new_m = re.sub(r'\s*[）\)]+\s*$', '', new_m)  # trailing close parens
        new_m = re.sub(r'\s*[（\(]+\s*$', '', new_m)  # trailing open parens
        new_m = new_m.strip().rstrip('，,;；:：、.>〉》')
        
        if new_m != m:
            tuition_fixed += 1
            rec['major'] = new_m
    
    print("Tuition cleaned: {}".format(tuition_fixed))
    
    # Final stats
    print("\n=== Final verification ===")
    corrupted_after = sum(1 for i, r in enumerate(data) if r.get('major','') and (r['major'].startswith('国家一流') or r['major'].startswith('合作方') or r['major'].startswith('单列专业')))
    db_after = sum(1 for r in data if '((' in r.get('major','') or chr(65288)*2 in r.get('major',''))
    campus_after = sum(1 for r in data if '办学地点' in r.get('major','') or '就读地点' in r.get('major',''))
    empty_after = sum(1 for r in data if not r.get('major','').strip())
    unbalanced_after = sum(1 for r in data if r.get('major','') and (r['major'].count('（') != r['major'].count('）') or r['major'].count('(') != r['major'].count(')')))
    
    print("Corrupted: {} | Double brackets: {} | Campus: {} | Empty: {} | Unbalanced: {}".format(
        corrupted_after, db_after, campus_after, empty_after, unbalanced_after))
    
    # Save
    d['meta']['fixes_quality_final'] = {
        "corrupted_restored": len(corrupted) if corrupted else 0,
        "tuition_cleaned": tuition_fixed,
        "generated_at": "2026-05-28 17:20:00"
    }
    
    with open(CLEANED, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False)
    print("\nSaved: {}".format(CLEANED))
    
    # Update report
    report = {}
    if os.path.exists(REPORT):
        with open(REPORT, 'r', encoding='utf-8') as f:
            report = json.load(f)
    report['quality_final'] = {
        "corrupted_restored": len(corrupted) if corrupted else 0,
        "tuition_cleaned": tuition_fixed,
        "timestamp": "2026-05-28 17:20:00"
    }
    with open(REPORT, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
