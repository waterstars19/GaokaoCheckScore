#!/usr/bin/env python3
"""Download model.bin from HF mirror with resume support"""
import os, sys, time
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '1'

from huggingface_hub import hf_hub_download

model_path = "D:\\GoakaoProject\\expert_advice\\whisper_model\\model.bin"
os.makedirs(os.path.dirname(model_path), exist_ok=True)

t0 = time.time()
print("下载 model.bin (~3.1GB)...")
try:
    path = hf_hub_download(
        repo_id='Systran/faster-whisper-large-v3',
        filename='model.bin',
        repo_type='model',
        resume=True,
        local_dir="D:\\GoakaoProject\\expert_advice\\whisper_model",
        local_dir_use_symlinks=False
    )
    elapsed = time.time() - t0
    size_mb = os.path.getsize(path) / 1024 / 1024
    print(f"✅ 下载完成: {path}")
    print(f"   大小: {size_mb:.0f} MB, 耗时: {elapsed:.0f}s")
except Exception as e:
    print(f"❌ 下载失败: {str(e)[:200]}")
