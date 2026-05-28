# -*- coding: utf-8 -*-
import json

with open('D:/GoakaoProject/data_985/985_schools_local.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Summary
total = len(data['schools'])
with_majors = sum(1 for s in data['schools'] if s['major_list'])
with_colleges = sum(1 for s in data['schools'] if s['college_list'])
majors_count = sum(len(s['major_list']) for s in data['schools'])
colleges_count = sum(len(s['college_list']) for s in data['schools'])

print('=== Final Summary ===')
print(f'985 schools found: {total}')
print(f'With major data: {with_majors}')
print(f'With college data: {with_colleges}')
print(f'Total unique majors: {majors_count}')
print(f'Total college references: {colleges_count}')
print()

# Schools with good college data (3+ valid)
print('=== Schools with good college listings (3+) ===')
for s in data['schools']:
    clist = s['college_list']
    if len(clist) >= 3:
        good = [c for c in clist 
                if len(c) >= 3 
                and c != s['school_name']
                and '年' not in c[:5]
                and '孔子' not in c
                and '继续教育' not in c
                and '网络教育' not in c]
        if len(good) >= 3:
            print(f'  {s["school_name"]}: {len(good)} colleges ({", ".join(good[:12])})')

print()
print('=== Top 10 schools by major count ===')
sorted_s = sorted(data['schools'], key=lambda x: len(x['major_list']), reverse=True)
for s in sorted_s[:10]:
    print(f'  {s["school_name"]}: {len(s["major_list"])} majors')

print()
print('=== All 985 schools ===')
for s in data['schools']:
    mcount = len(s['major_list'])
    ccount = len(s['college_list'])
    print(f'  {s["school_name"]}: majors={mcount}, colleges={ccount}')
