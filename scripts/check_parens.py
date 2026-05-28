import json
with open(r'D:\GoakaoProject\docs\admission_plans_cleaned.json','r',encoding='utf-8') as f:
    d = json.load(f)
data = d['data']

print('=== Unbalanced parens samples ===')
count = 0
for i, r in enumerate(data):
    m = r.get('major','')
    if not m:
        continue
    c_open = m.count(chr(65288)) + m.count('(')
    c_close = m.count(chr(65289)) + m.count(')')
    if c_open != c_close:
        count += 1
        if count <= 30:
            dif = c_open - c_close
            print(f'[{i}] open={c_open} close={c_close} diff={dif}')
            print(f'     major={m[:200]}')

print(f'\nTotal unbalanced: {count}')
