"""批量转写多个音频文件"""
import json
import os
import time
import sys
import librosa
from funasr import AutoModel

# 模型路径（已经在GPT-SoVITS下下载好了）
model_dir = r"D:\GPT-SoVITS\tools\asr\models\speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
vad_dir = r"D:\GPT-SoVITS\tools\asr\models\speech_fsmn_vad_zh-cn-16k-common-pytorch"
punc_dir = r"D:\GPT-SoVITS\tools\asr\models\punc_ct-transformer_zh-cn-common-vocab272727-pytorch"

os.environ["MODELSCOPE_CACHE"] = r"D:\GPT-SoVITS\tools\asr\models"

print("加载 FunASR Paraformer 模型...")
start = time.time()
model = AutoModel(
    model=model_dir,
    vad_model=vad_dir,
    punc_model=punc_dir,
    disable_update=True,
)
print(f"模型加载: {time.time() - start:.1f}s")

# 要转写的音频
audio_files = [
    r"D:\GoakaoProject\expert_advice\bilibili_videos\video1_张雪峰：家长你报志愿用豆包你疯啦？它懂啥啊.mp3",
    r"D:\GoakaoProject\expert_advice\bilibili_videos\video2_天津大学 南开大学怎么样#张雪峰高考志愿填报.mp3",
    r"D:\GoakaoProject\expert_advice\bilibili_videos\video3_张雪峰：2026高考志愿填报5大建议，分析的太透彻了！.mp3",
]

video_info = [
    {"num": 1, "title": "家长你报志愿用豆包你疯啦？它懂啥啊", "url": "https://www.bilibili.com/video/BV1psc8zrEFQ/"},
    {"num": 2, "title": "天津大学 南开大学怎么样#张雪峰高考志愿填报", "url": "https://www.bilibili.com/video/BV14vrDBdEzb/"},
    {"num": 3, "title": "张雪峰：2026高考志愿填报5大建议，分析的太透彻了！", "url": "https://www.bilibili.com/video/BV1pookBeEH1/"},
]

results = []

for idx, (audio_path, info) in enumerate(zip(audio_files, video_info)):
    print(f"\n===== [{idx+1}/3] 转写: {info['title']} =====")
    
    if not os.path.exists(audio_path):
        print(f"  文件不存在，跳过: {audio_path}")
        continue
    
    # 加载音频
    t0 = time.time()
    audio, sr = librosa.load(audio_path, sr=16000, mono=True)
    duration = len(audio) / sr
    print(f"  音频: {duration:.1f}s, {os.path.getsize(audio_path)/1024:.0f}KB")
    
    # 转写
    t1 = time.time()
    rec_result = model.generate(input=audio, disable_vad=False, disable_punc=False)
    t2 = time.time()
    
    if isinstance(rec_result, list) and len(rec_result) > 0:
        text = rec_result[0].get("text", "")
    else:
        text = str(rec_result)
    
    print(f"  转写耗时: {t2-t1:.1f}s")
    print(f"  结果预览: {text[:200]}...")
    
    result = {
        "num": info["num"],
        "title": info["title"],
        "url": info["url"],
        "duration": round(duration, 1),
        "full_text": text,
        "segments": []
    }
    
    if isinstance(rec_result, list):
        for seg in rec_result:
            result["segments"].append({
                "start": seg.get("start", 0),
                "end": seg.get("end", 0),
                "text": seg.get("text", "")
            })
    
    results.append(result)

# 保存全部结果
output_path = r"D:\GoakaoProject\expert_advice\bilibili_videos\all_transcripts.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n===== 全部完成 =====")
print(f"结果已保存: {output_path}")

# 打印摘要
print("\n--- 转写摘要 ---")
for r in results:
    print(f"\n## {r['title']}")
    print(f"时长: {r['duration']}s")
    print(f"全文: {r['full_text'][:300]}...")
