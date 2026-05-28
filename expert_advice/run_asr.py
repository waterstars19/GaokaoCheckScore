#!/usr/bin/env python3
"""ASR with faster-whisper via HF mirror"""
import os, time, json
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from faster_whisper import WhisperModel

t0 = time.time()

print("1/4 加载 Whisper large-v3 模型（~3GB，首次需下载）...")
model = WhisperModel('large-v3', device='cpu', compute_type='int8', num_workers=2)
print(f"   模型加载完成: {time.time()-t0:.1f}s")

print("2/4 转写音频...")
t1 = time.time()
segments, info = model.transcribe('bilibili_audio.mp3', language='zh', beam_size=5)
print(f"   转写完成: {time.time()-t1:.1f}s")
print(f"   语言: {info.language} (概率: {info.language_probability:.1%})")

print("\n3/4 输出分段结果:")
full_text = ''
all_segs = []
for seg in segments:
    s = round(seg.start, 1)
    e = round(seg.end, 1)
    t = seg.text.strip()
    print(f"  [{s:06.1f}s -> {e:06.1f}s] {t}")
    all_segs.append({'start': s, 'end': e, 'text': t})
    full_text += t + ' '

print(f"\n--- 全文 ---")
print(full_text.strip())

print("4/4 保存结果...")
with open('transcript_raw.json', 'w', encoding='utf-8') as f:
    json.dump({
        'source': 'https://b23.tv/813gSrk',
        'title': '评论区问题精选3，总有你关心的',
        'duration': 74.3,
        'segments': all_segs,
        'full_text': full_text.strip()
    }, f, ensure_ascii=False, indent=2)

print(f"\n✅ 原始转写已保存: transcript_raw.json ({len(full_text)} 字)")
print(f"   总耗时: {time.time()-t0:.1f}s")
