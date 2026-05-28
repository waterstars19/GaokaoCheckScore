"""Fix remaining 9 items manually"""
import json, re

LPA = chr(0xff08)
RPA = chr(0xff09)
DBL = LPA + LPA

with open(r'D:\GoakaoProject\docs\admission_plans_cleaned.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)
d = raw['data']

# Find and display remaining issues
print("=== Remaining issues ===")
for item in d:
    major = item.get('major', '') or ''
    if DBL in major:
        print(f'DOUBLE: major=[{major[:120]}]  school=[{item.get("school","?")}]')
    if any(k in major for k in ['元/年', '办学地点', '培养模式', '收费标准', '招生简章']):
        print(f'JUNK: major=[{major[:120]}]  school=[{item.get("school","?")}]')

# Fix them
for item in d:
    major = item.get('major', '') or ''
    
    # Fix double parens: 铁道运输类（（驾驶）、城市轨道车辆应用技术（检修）...）
    if DBL in major:
        # Extract inner content from double parens
        m = re.search(LPA + LPA + r'(.+?)' + RPA + RPA, major)
        if m:
            inner = m.group(1)
            existing = item.get('direction', '') or ''
            item['direction'] = (existing + '; ' + inner).strip('; ')
            # Remove double-paren portion
            major = major.replace(DBL + inner + RPA + RPA, '').replace(LPA + LPA + inner + RPA, '')
            item['major'] = major.strip()
    
    # Fix 元/年
    if '元/年' in major:
        idx = major.find('元/年')
        before = major[:idx].rstrip('；;，, ')
        # Remove the 元/年 part and anything after
        item['major'] = before
    
    # Fix other junk
    for kw in ['办学地点', '培养模式', '收费标准', '招生简章']:
        if kw in major:
            idx = major.find(kw)
            item['major'] = major[:idx].rstrip('；;，, ')

# Check remaining
remaining = 0
for item in d:
    major = item.get('major', '') or ''
    if DBL in major:
        remaining += 1
    if any(k in major for k in ['元/年', '办学地点', '培养模式', '收费标准', '招生简章']):
        remaining += 1

# Save
with open(r'D:\GoakaoProject\docs\admission_plans_cleaned.json', 'w', encoding='utf-8') as f:
    json.dump(raw, f, ensure_ascii=False, indent=2)

print(f'\nRemaining issues after fix: {remaining}')
