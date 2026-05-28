"""Check how backend pipeline works"""
import os, json, re

# Check app.py for which data source it loads
with open(r'D:\GoakaoProject\backend\app.py', 'r', encoding='utf-8') as f:
    app = f.read()

# Find all file paths
sources = set()
for m in re.findall(r"(?:PROCESSED_DIR|PROJECT_DIR|FRONTEND_DIR)\s*\+\s*['\"]([^'\"]+)", app):
    clean = m.replace("'", "").replace('"', "")
    if 'json' in clean.lower():
        sources.add(clean)

print("Backend loads these files from processed/ and docs/:")
for s in sorted(sources):
    full = os.path.join(r'D:\GoakaoProject', s)
    exists = 'EXISTS' if os.path.exists(full) else 'MISSING'
    sz = os.path.getsize(full) / 1024 / 1024 if os.path.exists(full) else 0
    print(f'  {s}  [{exists}] ({sz:.1f} MB)')

print()
print("These were generated FROM admission_plans.json via the scripts pipeline.")
print("So cleaning admission_plans.json alone won't update the API.")
print("We need to regenerate processed/ files to see the effect.")

# Check if extract_admission_plans.py references admission_plans.json
with open(r'D:\GoakaoProject\scripts\extract_admission_plans.py', 'r', encoding='utf-8') as f:
    ep = f.read()
if 'admission_plans' in ep:
    print()
    print("extract_admission_plans.py -> reads admission_plans.json")
    print("This is the pipeline entry point.")
