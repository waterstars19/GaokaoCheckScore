#!/usr/bin/env python3
"""Direct download of model.bin from HF mirror with progress bar"""
import requests, os, time, sys

url = 'https://hf-mirror.com/Systran/faster-whisper-large-v3/resolve/main/model.bin'
dest = 'D:\\GoakaoProject\\expert_advice\\whisper_model\\model.bin'
os.makedirs(os.path.dirname(dest), exist_ok=True)

# 检查是否有已下载的部分（断点续传）
headers = {}
if os.path.exists(dest):
    existing = os.path.getsize(dest)
    headers['Range'] = f'bytes={existing}-'
    mode = 'ab'
else:
    existing = 0
    mode = 'wb'

t0 = time.time()
resp = requests.get(url, stream=True, timeout=30, headers=headers)
total = int(resp.headers.get('Content-Length', 0)) + existing
downloaded = existing

print(f'总大小: {total/1024/1024:.0f} MB')
print(f'已下载: {downloaded/1024/1024:.1f} MB')
print(f'状态码: {resp.status_code}')

if resp.status_code == 416:  # Range not satisfiable - file is complete
    print('文件已完整下载！')
else:
    with open(dest, mode) as f:
        for chunk in resp.iter_content(chunk_size=1024*1024):  # 1MB chunks
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                elapsed = time.time() - t0
                speed = downloaded / elapsed / 1024 / 1024
                pct = downloaded / total * 100
                print(f'\r  {pct:.1f}% - {downloaded/1024/1024:.0f}/{total/1024/1024:.0f} MB - {speed:.1f} MB/s', end='')

print(f'\n✅ 下载完成: {dest}')
print(f'   {downloaded/1024/1024:.0f} MB, 耗时: {time.time()-t0:.0f}s')
