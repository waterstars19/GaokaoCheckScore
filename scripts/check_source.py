import json

with open(r'D:\GoakaoProject\docs\admission_plans.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
records = data['data']

# Find records where "办学地点" appears without parentheses  
no_paren_location = []
for r in records:
    m = r.get('major', '')
    # Check if 办学地点 exists but is NOT inside parentheses
    if '办学地点' in m:
        # Count chars before/after parens
        in_paren = False
        for i, ch in enumerate(m):
            if ch in '（(':
                in_paren = True
            elif ch in '）)':
                in_paren = False
            elif not in_paren and m[i:i+4] == '办学地点':
                no_paren_location.append(m)
                break

print(f'Records with "办学地点" NOT in parens: {len(no_paren_location)}')
for m in sorted(set(no_paren_location))[:20]:
    print(f'  [{m}]')

# Check empty major records in source
empty_count = sum(1 for r in records if not r.get('major', '').strip())
print(f'\nEmpty major in source: {empty_count}')

# Find records where major contains "学费" not in parens
no_paren_tuition = []
for r in records:
    m = r.get('major', '')
    if '学费' in m:
        in_paren = False
        for i, ch in enumerate(m):
            if ch in '（(':
                in_paren = True
            elif ch in '）)':
                in_paren = False
            elif not in_paren and m[i:i+2] == '学费':
                no_paren_tuition.append(m)
                break

print(f'\nRecords with "学费" NOT in parens: {len(no_paren_tuition)}')
for m in sorted(set(no_paren_tuition))[:20]:
    print(f'  [{m}]')
