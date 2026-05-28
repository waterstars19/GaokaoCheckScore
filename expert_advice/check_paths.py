"""Check file paths used in backend app.py"""
import os

with open(r'D:\GoakaoProject\backend\app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    line = line.strip()
    if ('open(' in line or 'FileResponse' in line) and '.json' in line:
        print(f'L{i+1}: {line[:150]}')
