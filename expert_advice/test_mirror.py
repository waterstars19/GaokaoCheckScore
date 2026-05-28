#!/usr/bin/env python3
"""Test HuggingFace mirror access"""
import os, urllib.request

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
print(f'HF_ENDPOINT = {os.environ["HF_ENDPOINT"]}')

from huggingface_hub import HfApi
api = HfApi()
try:
    info = api.repo_info('Systran/faster-whisper-large-v3', repo_type='model')
    print(f'✅ Systran/faster-whisper-large-v3 可达')
    print(f'   模型大小: {info.siblings[0].size if info.siblings else "未知"}')
    print(f'   文件数: {len(info.siblings)}')
except Exception as e:
    print(f'❌ 无法获取: {str(e)[:200]}')
