import json

with open(r'D:\GoakaoProject\docs\admission_plans_cleaned.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
records = data['data']
meta = data['meta']

print("=== META ===")
for k, v in meta.items():
    print(f"  {k}: {v}")

# Check preserved modifiers
preserved_check = ['师范', '中外合作办学', '实验班', '卓越班', '基地班', '创新班', '民族班', '定向', '免费', '国家专项', '地方专项']
counts = {kw: 0 for kw in preserved_check}
for r in records:
    m = r.get('major', '')
    for kw in preserved_check:
        if kw in m:
            counts[kw] += 1

print('\n=== PRESERVED MODIFIER COUNTS IN CLEANED DATA ===')
for kw, c in sorted(counts.items(), key=lambda x: -x[1]):
    print(f'  {kw}: {c:,}')

# Show examples
print('\n=== EXAMPLES WITH PRESERVED MODIFIERS ===')
for kw in ['师范', '中外合作办学', '实验班']:
    count = 0
    for r in records:
        if kw in r.get('major', '') and count < 3:
            print(f'  [{r["major"]}]  school={r["school"]}')
            count += 1

# Check direction field presence
with_direction = sum(1 for r in records if r.get('direction'))
print(f'\n=== DIRECTION FIELD ===')
print(f'  Records with direction: {with_direction:,}')
# Show random directions
for r in records:
    d = r.get('direction')
    if d and len(d) > 0:
        print(f'  [{r["major"]}] -> dir=[{d}]')
    if sum(1 for x in records if x.get('direction')) < 10:
        break

# Show 10 random samples
print('\n=== RANDOM SAMPLES ===')
import random
samples = random.sample(records, min(10, len(records)))
for r in samples:
    print(f'  major=[{r["major"]}] tuition={r.get("tuition")} duration={r.get("duration")} dir={r.get("direction", "N/A")}')

# Check total size
print(f'\nTotal cleaned records: {len(records):,}')
