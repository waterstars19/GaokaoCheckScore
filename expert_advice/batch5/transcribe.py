import json, os, librosa, glob, time
from funasr import AutoModel

MODEL_DIR = r"D:\GPT-SoVITS\tools\asr\models\speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
VAD_DIR = r"D:\GPT-SoVITS\tools\asr\models\speech_fsmn_vad_zh-cn-16k-common-pytorch"
PUNC_DIR = r"D:\GPT-SoVITS\tools\asr\models\punc_ct-transformer_zh-cn-common-vocab272727-pytorch"
os.environ["MODELSCOPE_CACHE"] = r"D:\GPT-SoVITS\tools\asr\models"

md = AutoModel(model=MODEL_DIR, vad_model=VAD_DIR, punc_model=PUNC_DIR, disable_update=True)

audio_dir = r"D:\GoakaoProject\expert_advice\batch5"
files = sorted(glob.glob(os.path.join(audio_dir, "*.mp3")))
results = []
for path in files:
    bn = os.path.basename(path)
    print(f"Transcribing {bn}...")
    audio, sr = librosa.load(path, sr=16000, mono=True)
    dur = len(audio)/sr
    t0 = time.time()
    r = md.generate(input=audio, disable_vad=False, disable_punc=False)
    text = r[0].get("text", "") if isinstance(r, list) and len(r) > 0 else str(r)
    print(f"  {dur:.0f}s -> {len(text)} chars ({time.time()-t0:.1f}s)")
    results.append({"file": bn, "duration": round(dur,1), "full_text": text})
    
out_path = os.path.join(audio_dir, "all_transcripts.json")
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"Saved to {out_path}")
