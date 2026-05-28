"""Check cleaned data structure"""
import json
with open(r'D:\GoakaoProject\docs\admission_plans_cleaned.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f'Top-level type: {type(data).__name__}')
if isinstance(data, dict):
    print(f'Keys: {list(data.keys())[:5]}')
    # It might be nested under a key
    for k, v in data.items():
        if isinstance(v, list):
            print(f'Length of [{k}]: {len(v)}')
            if len(v) > 0:
                print(f'First item type: {type(v[0]).__name__}')
                if isinstance(v[0], dict):
                    print(f'First item keys: {list(v[0].keys())[:10]}')
                break
elif isinstance(data, list):
    print(f'Length: {len(data)}')
    if len(data) > 0:
        print(f'First item type: {type(data[0]).__name__}')
        if isinstance(data[0], dict):
            print(f'First item keys: {list(data[0].keys())[:10]}')
        else:
            print(f'First item: {str(data[0])[:200]}')
