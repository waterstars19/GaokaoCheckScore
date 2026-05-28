"""使用 ModelScope 的 Paraformer 模型进行中文语音识别（不使用 funasr 包）"""
import json
import os
import time
import sys

# 设置环境变量避免一些警告
os.environ["MODELSCOPE_CACHE"] = os.path.join(os.path.dirname(__file__), "models_cache")

input_audio = sys.argv[1] if len(sys.argv) > 1 else r"D:\GoakaoProject\expert_advice\bilibili_audio.mp3"
output_json = sys.argv[2] if len(sys.argv) > 2 else r"D:\GoakaoProject\expert_advice\funasr_transcript.json"

print(f"音频文件: {input_audio}")
print(f"输出文件: {output_json}")

# 为确保音频是 16kHz，先检查并转换
import librosa
import soundfile as sf

print("加载音频...")
audio, sr = librosa.load(input_audio, sr=16000, mono=True)
duration = len(audio) / sr
print(f"音频时长: {duration:.1f}s, 采样率: {sr}Hz")

# 使用 modelscope 的 pipeline
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

print("加载 Paraformer 模型（首次会从 ModelScope 自动下载）...")
start = time.time()

inference_pipeline = pipeline(
    task=Tasks.auto_speech_recognition,
    model='damo/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch',
    model_revision='v2.0.4',
)

print(f"模型加载完成: {time.time() - start:.1f}s")

print("转写中...")
rec_result = inference_pipeline(audio_in=input_audio)
print(f"转写完成: {time.time() - start:.1f}s")

# 处理结果
if isinstance(rec_result, dict):
    text = rec_result.get('text', '')
    segments = []
    
    # 如果有时间戳信息
    if 'timestamp' in rec_result:
        for ts in rec_result['timestamp']:
            segments.append({
                "start": ts.get('start', 0),
                "end": ts.get('end', 0),
                "text": ts.get('text', '')
            })
    else:
        segments.append({
            "start": 0,
            "end": duration,
            "text": text
        })
    
    output = {
        "source": "https://b23.tv/813gSrk",
        "title": "评论区问题精选3，总有你关心的",
        "duration": duration,
        "language": "zh",
        "model": "Paraformer-large (ModelScope)",
        "segments": segments,
        "full_text": text
    }
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n===== 转写结果 =====")
    print(text)
    print(f"\n结果已保存到: {output_json}")
    print(f"总耗时: {time.time() - start:.1f}s")
else:
    print(f"转写结果类型: {type(rec_result)}")
    print(rec_result)
