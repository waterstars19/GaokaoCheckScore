import json
with open(r'D:\GoakaoProject\docs\admission_plans_cleaned.json','r',encoding='utf-8') as f:
    d = json.load(f)
data = d['data']

print('=== Double bracket fixes ===')
check_indices = [4022, 6335, 31271, 67906, 68416, 69169, 70184, 70204, 70802, 71119, 71547, 71602, 72404, 72409, 72418, 72424]
for idx in check_indices:
    if idx < len(data):
        r = data[idx]
        maj = r.get('major','')
        dire = r.get('direction','')
        print(f"[{idx}] major={maj[:150]}")
        if dire:
            print(f"     direction={dire[:150]}")

print('\n=== Campus fixes ===')
campus_check = [138916, 139620, 140521, 141543, 166834, 192230, 217367, 218970]
for idx in campus_check:
    if idx < len(data):
        r = data[idx]
        maj = r.get('major','')
        print(f"[{idx}] major={maj[:200]}")

print('\n=== Empty major fixes (sample) ===')
empty_samples = [114765, 138499, 138512]
for idx in empty_samples:
    if idx < len(data):
        r = data[idx]
        maj = r.get('major','')
        sch = r.get('school','')
        print(f"[{idx}] major={maj[:100]} school={sch}")

# Also check some known problem records
print('\n=== Specific problem checks ===')
# Check the car manufacturing one
for i, r in enumerate(data):
    m = r.get('major','')
    if '汽车制造类' in m and '中外' in m:
        print(f"[{i}] major={m}")
        print(f"     direction={r.get('direction','')}")
        break

for i, r in enumerate(data):
    m = r.get('major','')
    if '应用化学' == m or '应用化学（' in m:
        sch = r.get('school','')
        if '基地' in m or '核科学' in str(r.get('direction','')):
            print(f"[{i}] major={m} school={sch}")
            print(f"     direction={r.get('direction','')}")
