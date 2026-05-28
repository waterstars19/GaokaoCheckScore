"""Check admission_plans for duplicate major entries with garbage in names"""
import json
import re
from collections import defaultdict

with open(r'D:\GoakaoProject\docs\admission_plans.json', 'r', encoding='utf-8') as f:
    ap = json.load(f)
d = ap['data']

print(f"Total records: {len(d)}")

# Find descriptive info in major names
cnt_specific = 0
for item in d:
    major = item.get('major', '')
    if re.search(r'学费|元/年|学制|年制|培养|方向|色盲|色弱|体检', major):
        if cnt_specific < 15:
            tuition = item.get('tuition')
            duration = item.get('duration')
            print(f'  {major[:120]} | tuition={tuition} | duration={duration}')
        cnt_specific += 1
print(f'\nDescriptive info in major names: {cnt_specific}')

# Group by school + major_code, find duplicates
print('\n=== Grouping by school + major_code ===')
grouped = defaultdict(set)
for item in d:
    s = item.get('school', '')
    mc = item.get('major_code', '')
    major = item.get('major', '')
    if mc and mc != '0':
        grouped[(s, mc)].add(major)

dup_examples = 0
for (s, mc), names in grouped.items():
    if len(names) > 1:
        pure = [n for n in names if '(' not in n and '(' not in n]
        extra = [n for n in names if '(' in n or '(' in n]
        if pure and extra:
            if dup_examples < 8:
                print(f'\n  {s} | code={mc}')
                for n in sorted(names)[:4]:
                    print(f'    - {n}')
            dup_examples += 1
            
print(f'\nDuplicate groups (pure + extra): {dup_examples}')

# Also check for double parentheses like "（（xxx））"
double_paren = 0
for item in d:
    major = item.get('major', '')
    if '((' in major or '(（' in major or '（(' in major or '（（' in major:
        if double_paren < 5:
            print(f'\n  Double parens: {major[:100]}')
        double_paren += 1
print(f'\nDouble parentheses entries: {double_paren}')
