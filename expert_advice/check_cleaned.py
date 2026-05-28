"""Check remaining issues in cleaned data"""
import json

LPA = chr(0xff08)  # fullwidth (
RPA = chr(0xff09)  # fullwidth )
LPA2 = chr(0x0028) # ascii (
DBL1 = LPA + LPA
DBL2 = LPA2 + LPA2

JUNK_TERMS = ['\u5143/\u5e74', '\u529e\u5b66\u5730\u70b9', '\u8be6\u7ec6\u57f9\u517b',
              '\u6536\u8d39\u6807\u51c6', '\u62db\u751f\u7b80\u7ae0', '\u57f9\u517b\u6a21\u5f0f']

with open(r'D:\GoakaoProject\docs\admission_plans_cleaned.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)

d = raw['data'] if isinstance(raw, dict) and 'data' in raw else raw
print(f'Total: {len(d)}')

double_parens = []
junk_majors = []
empty_majors = []
direction_items = []

for item in d:
    major = item.get('major', '') or ''
    direction = item.get('direction', '') or ''
    if direction:
        if len(direction_items) < 3:
            direction_items.append(item)
    if major.strip() == '':
        if len(empty_majors) < 5:
            empty_majors.append(item)
    elif (DBL1 in major) or (DBL2 in major):
        if len(double_parens) < 8:
            double_parens.append(item)
    elif any(k in major for k in JUNK_TERMS):
        if len(junk_majors) < 8:
            junk_majors.append(item)

print('\n=== direction field examples ===')
for d_ in direction_items:
    print(f'  major={d_.get("major","?")}  direction={d_.get("direction","?")}')

print('\n=== remaining double parentheses ===')
for d_ in double_parens:
    print(f'  major={d_.get("major","?")[:80]}  school={d_.get("school","?")}  code={d_.get("major_code","?")}')

print('\n=== remaining junk names ===')
for d_ in junk_majors:
    print(f'  major={d_.get("major","?")[:100]}  school={d_.get("school","?")}')

print('\n=== empty majors ===')
for d_ in empty_majors:
    print(f'  school={d_.get("school","?")}  code={d_.get("major_code","?")}  batch={d_.get("batch","?")}  year={d_.get("year","?")}')

# Actual counts
dp = sum(1 for item in d if (DBL1 in (item.get('major','') or '')) or (DBL2 in (item.get('major','') or '')))
ji = sum(1 for item in d if any(k in (item.get('major','') or '') for k in JUNK_TERMS))
em = sum(1 for item in d if not (item.get('major','') or '').strip())
di = sum(1 for item in d if item.get('direction', ''))

print(f'\n=== Summary ===')
print(f'Direction extracted: {di}')
print(f'Remaining double parens: {dp}')
print(f'Remaining junk: {ji}')
print(f'Empty major names: {em}')
print(f'Cleaned file: D:\\GoakaoProject\\docs\\admission_plans_cleaned.json')
