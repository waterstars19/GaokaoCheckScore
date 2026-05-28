#!/usr/bin/env python3
"""ASR with faster-whisper using ffmpeg for audio decoding"""
import subprocess
import numpy as np
import time
from faster_whisper import WhisperModel

t0 = time.time()

# Use ffmpeg to decode audio to raw PCM
print("解码音频...")
cmd = [
    'ffmpeg', '-i', 'bilibili_audio.mp3',
    '-f', 's16le', '-acodec', 'pcm_s16le',
    '-ar', '16000', '-ac', '1', '-loglevel', 'error', '-'
]
out = subprocess.run(cmd, capture_output=True).stdout
audio = np.frombuffer(out, dtype=np.int16).astype(np.float32) / 32768.0
print(f"  音频加载完成: {len(audio)/16000:.1f}秒")

# Transcribe
print("加载模型 large-v3...")
model = WhisperModel('large-v3', device='cpu', compute_type='int8')

print("转写中...")
segments, info = model.transcribe(audio, language='zh', beam_size=5)
print(f"\n检测到语言: {info.language} (概率: {info.language_probability:.2%})")
print()

# Collect results
full_text = ''
all_segments = []
for seg in segments:
    start = seg.start
    end = seg.end
    text = seg.text.strip()
    print(f'[{start:06.1f}s - {end:06.1f}s] {text}')
    all_segments.append({'start': round(start, 1), 'end': round(end, 1), 'text': text})
    full_text += text + ' '

print(f'\n--- 全文 ---')
print(full_text.strip())

# Save raw transcript
import json
with open('transcript_raw.json', 'w', encoding='utf-8') as f:
    json.dump({
        'source': 'https://b23.tv/813gSrk',
        'title': '评论区问题精选3，总有你关心的',
        'duration': round(len(audio)/16000, 1),
        'segments': all_segments,
        'full_text': full_text.strip()
    }, f, ensure_ascii=False, indent=2)
print(f'\n✅ 原始转写已保存: transcript_raw.json')
print(f'处理总耗时: {time.time()-t0:.1f}秒')
