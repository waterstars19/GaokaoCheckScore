"""
FunASR 中文语音转写脚本 v2
使用 Paraformer 模型对 B站音频进行中文语音识别
修复输出格式：去除字间空格，按时间戳分段
"""
import json
import time
import re
import torch
from funasr import AutoModel

AUDIO_PATH = r"D:\GoakaoProject\expert_advice\bilibili_audio.mp3"
OUTPUT_PATH = r"D:\GoakaoProject\expert_advice\funasr_transcript.json"

print(f"CUDA available: {torch.cuda.is_available()}")

print("Loading Paraformer model...")
start_load = time.time()

model = AutoModel(
    model="iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
    device="cuda:0" if torch.cuda.is_available() else "cpu",
    hub="ms",
    disable_update=True,
)

print(f"Model loaded in {time.time() - start_load:.1f}s")
print(f"Transcribing: {AUDIO_PATH}")

start_trans = time.time()
result = model.generate(
    input=AUDIO_PATH,
    batch_size_s=300,
    return_raw_text=False,  # was True, let model do its thing
)
elapsed = time.time() - start_trans
print(f"Transcription done in {elapsed:.1f}s (RTF: {elapsed/74.3:.3f})")

# Parse result
res = result[0]
raw_text = res.get("text", "")
timestamps = res.get("timestamp", [])  # [[start_ms, end_ms], ...]

print(f"Raw text length: {len(raw_text)} chars")
print(f"Timestamps count: {len(timestamps)}")

# Remove spaces between Chinese characters
# The model outputs: "报 志 愿 吗 谁 还 不 中" etc.
# Remove spaces that are between Chinese chars or punctuation
clean_text = re.sub(r'\s+', '', raw_text)  # Remove all spaces

print(f"Clean text length: {len(clean_text)} chars")

# Build segments from timestamps
# Default: one segment per timestamp entry
segments = []
for i, ts in enumerate(timestamps):
    seg_text = ""
    if i < len(timestamps):
        # Estimate characters per segment
        chars_per_seg = len(clean_text) // len(timestamps) if timestamps else 1
        start_idx = i * chars_per_seg
        end_idx = min(start_idx + chars_per_seg, len(clean_text))
        seg_text = clean_text[start_idx:end_idx]
    
    segments.append({
        "id": i,
        "text": seg_text,
        "start": ts[0] / 1000.0 if ts and ts[0] is not None else None,
        "end": ts[1] / 1000.0 if ts and ts[1] is not None else None,
    })

# Also try to do smart sentence splitting based on Chinese punctuation
# Use VAD timestamps to group into sentences
sentences = []
current_sent = ""
sent_start = None
sent_end = None

# 按时间戳逐条处理，收集成句子
for i, ts in enumerate(timestamps):
    chars_per_seg = len(clean_text) // len(timestamps)
    start_idx = i * chars_per_seg
    end_idx = min(start_idx + chars_per_seg, len(clean_text))
    chunk = clean_text[start_idx:end_idx]
    
    if not chunk:
        continue
    
    if not current_sent:
        sent_start = ts[0] / 1000.0
    
    current_sent += chunk
    sent_end = ts[1] / 1000.0 if ts[1] else None

# Add final sentence
if current_sent:
    sentences.append({
        "text": current_sent,
        "start": sent_start,
        "end": sent_end,
    })

output = {
    "source": "funasr_paraformer",
    "audio_file": AUDIO_PATH,
    "audio_duration_s": 74.3,
    "model": "iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
    "processing_time_s": elapsed,
    "language": "zh",
    "segments": segments,
    "full_text": clean_text,
    "segment_count": len(segments),
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nSaved to: {OUTPUT_PATH}")
print(f"Segments: {len(segments)}, Full text: {len(clean_text)} chars")
print(f"\n--- Full transcript ---")
# 按正常中文标点分段显示
# 尝试智能断句 - 每30个字左右一段
for i in range(0, len(clean_text), 35):
    print(clean_text[i:i+35])
