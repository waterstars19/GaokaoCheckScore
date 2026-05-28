import json
with open(r'D:\GoakaoProject\docs\admission_plans_cleaned.json','r',encoding='utf-8') as f:
    d = json.load(f)
data = d['data']

print('=== Key spot checks ===')
check = [
    (224, 'automotive'), (3473, 'applied-chem'), (4022, 'chem-pharma'),
    (67906, 'stats'), (68416, 'clinical-med'), (69169, 'history'),
    (70184, 'chemistry'), (70802, 'engineering'), (71119, 'eng-experiment'),
    (72404, 'chemistry2'), (138916, 'clinical-bachelor'), 
    (139620, 'esports'), (217367, 'clinical2'),
]
for idx, hint in check:
    if idx < len(data):
        r = data[idx]
        maj = r.get('major','')
        dire = r.get('direction','')
        print('\n[{}] ({})'.format(idx, hint))
        print('  major: {}'.format(maj[:200]))
        if dire:
            print('  direction: {}'.format(dire[:200]))

print('\n=== Overall stats ===')
empty = sum(1 for r in data if not r.get('major','').strip())
db = sum(1 for r in data if '((' in r.get('major','') or chr(65288)*2 in r.get('major',''))
campus = sum(1 for r in data if '办学地点' in r.get('major','') or '就读地点' in r.get('major',''))
c1 = sum(1 for r in data if r.get('major','') and r['major'].count(chr(65288)) != r['major'].count(chr(65289)))
c2 = sum(1 for r in data if r.get('major','') and r['major'].count('(') != r['major'].count(')'))

print('Empty majors: {}'.format(empty))
print('Double brackets: {}'.format(db))
print('Campus in major: {}'.format(campus))
print('Unbalanced full-width: {}'.format(c1))
print('Unbalanced half-width: {}'.format(c2))

# Also check the original double-bracket examples
print('\n=== Original problem examples ===')
for i, r in enumerate(data):
    m = r.get('major','')
    if m == '汽车制造类（中外合作办学）':
        print('[{}] major={} direction={}'.format(i, m, r.get('direction','')))
    if '核科学与技术基地班' in str(r.get('direction','')):
        print('[{}] major={} direction={} school={}'.format(i, m, r.get('direction',''), r.get('school','')))

# Sample a few "unknown major" records
unknown_count = 0
for r in data:
    if r.get('major','') == '未知专业':
        unknown_count += 1
        if unknown_count <= 3:
            print('Unknown: {}'.format(json.dumps(r, ensure_ascii=False)[:200]))
print('Total unknown major: {}'.format(unknown_count))

# Meta
meta_str = json.dumps(d.get('meta',{}), ensure_ascii=False, indent=2)
print('\nMeta: {}'.format(meta_str[:1000]))
