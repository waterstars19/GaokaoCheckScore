"""使用 FunASR (Paraformer) 进行中文语音识别，修正 API 调用"""
import json
import os
import time
import sys
import librosa

input_audio = sys.argv[1] if len(sys.argv) > 1 else r"D:\GoakaoProject\expert_advice\bilibili_audio.mp3"
output_json = sys.argv[2] if len(sys.argv) > 2 else r"D:\GoakaoProject\expert_advice\funasr_transcript.json"

print(f"音频: {input_audio}")
print(f"输出: {output_json}")

# 设置模型缓存到 GPT-SoVITS 目录
os.environ["MODELSCOPE_CACHE"] = r"D:\GPT-SoVITS\tools\asr\models"
os.environ["MODELSCOPE_MODELS"] = r"D:\GPT-SoVITS\tools\asr\models"

# 加载音频为 numpy array
print("加载音频...")
audio, sr = librosa.load(input_audio, sr=16000, mono=True)
duration = len(audio) / sr
print(f"时长: {duration:.1f}s, 采样率: {sr}Hz")

from funasr import AutoModel

start = time.time()

# Paraformer 模型路径
model_dir = r"D:\GPT-SoVITS\tools\asr\models\speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
vad_dir = r"D:\GPT-SoVITS\tools\asr\models\speech_fsmn_vad_zh-cn-16k-common-pytorch"
punc_dir = r"D:\GPT-SoVITS\tools\asr\models\punc_ct-transformer_zh-cn-common-vocab272727-pytorch"

print("加载 FunASR Paraformer 模型（含 VAD + 标点）...")
model = AutoModel(
    model=model_dir,
    vad_model=vad_dir,
    punc_model=punc_dir,
    disable_update=True,  # 不检查更新
)

print(f"模型加载: {time.time() - start:.1f}s")

# 使用音频数据而非文件路径（修复新版 funasr 的 bug）
print("转写中...")
rec_result = model.generate(input=audio, disable_vad=False, disable_punc=False)
print(f"转写完成: {time.time() - start:.1f}s")

# 处理结果
if isinstance(rec_result, list) and len(rec_result) > 0:
    text = rec_result[0].get("text", "")
else:
    text = str(rec_result)

output = {
    "source": "https://b23.tv/813gSrk",
    "title": "评论区问题精选3，总有你关心的",
    "duration": duration,
    "language": "zh",
    "model": "FunASR Paraformer-large + VAD + Punc",
    "segments": [],
    "full_text": text
}

# 尝试获取分段信息
if isinstance(rec_result, list):
    for i, seg in enumerate(rec_result):
        output["segments"].append({
            "start": seg.get("start", 0),
            "end": seg.get("end", 0),
            "text": seg.get("text", "")
        })

with open(output_json, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n===== FunASR 转写结果 =====")
print(text)
print(f"\n结果已保存: {output_json}")
print(f"总耗时: {time.time() - start:.1f}s")
