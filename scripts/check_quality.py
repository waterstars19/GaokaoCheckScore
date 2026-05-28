import json

with open(r'D:\GoakaoProject\docs\admission_plans_cleaned.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
recs = data['data']

# Check remaining double parens
double = [(r['major'], r.get('direction')) for r in recs if '（（' in r.get('major', '')]
print(f'Records with double-parens remaining: {len(double)}')
for m, d in double[:20]:
    print(f'  [{m}] dir=[{d}]')

# Check empty parens
empty_paren = [(r['major'], r.get('direction')) for r in recs if '（）' in r.get('major', '')]
print(f'\nRecords with empty parens: {len(empty_paren)}')
for m, d in empty_paren[:10]:
    print(f'  [{m}] dir=[{d}]')

# Check records with "招生" in major - indicators of corruption
corrupt = [(r['major'], r.get('school','')) for r in recs if '办学地点' in r.get('major', '') or '元/年' in r.get('major', '')]
print(f'\nRecords with junk still in major: {len(corrupt)}')
for m, s in corrupt[:10]:
    print(f'  [{m}] school={s}')

# Stats on major uniqueness
from collections import Counter
major_counts = Counter(r['major'] for r in recs)
print(f'\nUnique majors: {len(major_counts)}')
top = major_counts.most_common(20)
print('Top 20 most common majors:')
for m, c in top:
    print(f'  {c:>6d}: {m}')
