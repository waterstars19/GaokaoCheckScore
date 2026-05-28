"""Final fix for remaining issues in admission_plans_cleaned.json"""
import json, re

LPA = chr(0xff08)  # （
RPA = chr(0xff09)  # ）
DBL = LPA + LPA
JUNK_PATTERNS = [
    (re.compile(r'办学地点.*'), ''),
    (re.compile(r'元/年.*'), ''),
    (re.compile(r'\uff1b.*'), '；'),  # remove semicolon and everything after if it's junk
]

filepath = r'D:\GoakaoProject\docs\admission_plans_cleaned.json'
with open(filepath, 'r', encoding='utf-8') as f:
    raw = json.load(f)

d = raw['data'] if isinstance(raw, dict) and 'data' in raw else raw

fixes = {'double_parens_fixed': 0, 'junk_removed': 0}

for item in d:
    major = item.get('major', '') or ''
    modified = False
    
    # 1. Fix remaining double parentheses
    if DBL in major:
        # Extract inner content of （（...））
        m = re.search(LPA + LPA + r'(.+?)' + RPA + RPA, major)
        if m:
            inner = m.group(1)
            # check if inner is a direction (not a reserved term)
            reserved = ['中外合作办学', '师范', '师范类', '实验班', '卓越班', 
                       '基地班', '创新班', '民族班', '定向', '免费', 
                       '国家专项', '地方专项']
            should_extract = not any(r in inner for r in reserved)
            if should_extract:
                # Move to direction field
                existing_dir = item.get('direction', '') or ''
                if existing_dir:
                    item['direction'] = existing_dir + '; ' + inner
                else:
                    item['direction'] = inner
                # Remove the double-paren content from major
                old_major = major
                major = major.replace(f'{DBL}{inner}{RPA}{RPA}', '').replace(f'{DBL}{inner}{RPA}', '')
                # Also clean up possible trailing junk
                major = major.strip()
                item['major'] = major
                fixes['double_parens_fixed'] += 1
                modified = True
    
    # 2. Fix junk in major names
    if not modified:
        for pattern, replacement in JUNK_PATTERNS:
            new_major = pattern.sub(replacement, major).strip()
            if new_major != major:
                major = new_major
                item['major'] = major
                fixes['junk_removed'] += 1
                break
    
    # 3. Special case: "元/年" without proper context
    if '元/年' in major:
        # Remove trailing "元/年" and after
        idx = major.find('元/年')
        if idx > 0:
            prefix = major[:idx].strip()
            # Check if there's content before the pattern
            prefix = prefix.rstrip('；;，, ')
            item['major'] = prefix
            fixes['junk_removed'] += 1

# Save
with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(raw, f, ensure_ascii=False, indent=2)

print(f"Double parens fixed: {fixes['double_parens_fixed']}")
print(f"Junk removed: {fixes['junk_removed']}")

# Final count
dp = sum(1 for item in d if DBL in (item.get('major','') or ''))
ji = sum(1 for item in d if any(k in (item.get('major','') or '') for k in ['元/年', '办学地点', '培养模式', '收费标准', '招生简章']))
em = sum(1 for item in d if not (item.get('major','') or '').strip())
print(f"\nFinal remaining: double_parens={dp}, junk={ji}, empty={em}")
print(f"Total records: {len(d)}")
