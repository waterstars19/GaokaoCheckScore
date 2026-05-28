"""Find all JSON data loading in backend"""
import re

with open(r'D:\GoakaoProject\backend\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find os.path.join with .json
lines = content.split('\n')
for i, line in enumerate(lines):
    if '.json' in line.lower() and ('join' in line or 'open' in line or 'load' in line):
        print(f'{i+1}: {line.strip()[:200]}')