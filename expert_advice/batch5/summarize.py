import json, subprocess, os, re

def parse_output(text):
    """Try multiple ways to extract JSON from LLM output."""
    # Strip markdown code fences
    cleaned = text.strip()
    m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', cleaned, re.DOTALL)
    if m:
        cleaned = m.group(1).strip()
    # Try direct JSON
    try: return json.loads(cleaned)
    except: pass
    # Try loading outer object then content
    try:
        outer = json.loads(cleaned)
        if isinstance(outer, dict) and 'content' in outer:
            inner = outer['content'].strip()
            m2 = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', inner, re.DOTALL)
            if m2: inner = m2.group(1).strip()
            try: return json.loads(inner)
            except: pass
    except: pass
    return None

SYSTEM = "你是一个高考志愿填报专家分析工具。请将以下张雪峰视频的原始语音转写文本，处理成结构化的专家意见数据。要求：1.去掉口语化表达 2.保留核心观点 3.标注关键词标签 4.输出纯JSON，不要用markdown代码块包裹。格式：{\"video_title\":\"\", \"video_url\":\"\", \"duration_seconds\":0, \"topics\":[], \"keywords\":[], \"expert_opinions\":[{\"point\":\"\",\"detail\":\"\",\"tags\":[]}], \"actionable_advice\":[]}"

with open(r"D:\GoakaoProject\expert_advice\batch5\all_transcripts.json", 'r', encoding='utf-8') as f:
    data = json.load(f)

# Load existing results
existing_path = r"D:\GoakaoProject\expert_advice\batch5\expert_summary.json"
existing = {}
if os.path.exists(existing_path):
    with open(existing_path, 'r', encoding='utf-8') as f:
        existing = json.load(f)
existing_results = existing.get('videos', [])

results = []
for i, v in enumerate(data):
    # Check if we already have a good result
    if i < len(existing_results):
        prev = existing_results[i]
        if 'expert_opinions' in prev and prev.get('expert_opinions'):
            print(f"[{i+1}/{len(data)}] {v['file']} - SKIP (already done)")
            results.append(prev)
            continue
        if 'raw' in prev:
            print(f"[{i+1}/{len(data)}] {v['file']} - RETRY (parse failed)")
        else:
            print(f"[{i+1}/{len(data)}] {v['file']} - RETRY")
    else:
        print(f"[{i+1}/{len(data)}] {v['file']}...")
    
    # Build user message - truncate if too long
    full_text = v['full_text']
    if len(full_text) > 8000:
        full_text = full_text[:8000] + "...(truncated)"
    
    user = f"视频标题: {v['file']}\n视频时长: {v['duration']}秒\nURL: https://www.bilibili.com/video/BVxxx/\n\n转写全文:\n{full_text}"
    
    msg_file = os.path.join(r"D:\GoakaoProject\expert_advice\batch5", "_msg.json")
    with open(msg_file, 'w', encoding='utf-8') as f:
        json.dump([{"role":"system","content":SYSTEM},{"role":"user","content":user}], f, ensure_ascii=False)
    
    cmd = f'mmx text chat --model MiniMax-M2.7-highspeed --messages-file "{msg_file}" --output json --quiet --non-interactive --max-tokens 4096 --temperature 0.3'
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, encoding='utf-8', shell=True)
    
    if proc.returncode != 0:
        results.append({"video_title": v["file"], "error": proc.stderr[:200]})
        print(f"  ERROR: {proc.stderr[:100]}")
        continue
    
    stdout = proc.stdout.strip()
    rj = parse_output(stdout)
    
    if rj and isinstance(rj, dict) and ('expert_opinions' in rj or 'topics' in rj):
        results.append(rj)
        n_ops = len(rj.get('expert_opinions', []))
        n_topics = len(rj.get('topics', []))
        print(f"  OK - {n_ops} opinions, {n_topics} topics")
    else:
        # Save raw for debugging
        print(f"  PARSE FAIL, raw preview: {stdout[:150]}")
        results.append({"video_title": v["file"], "raw": stdout[:800], "raw_full": stdout})

out = {"source":"B站张雪峰视频","transcribe":"FunASR Paraformer","summary":"MiniMax-M2.7-highspeed","total":len(data),"videos":results}
with open(existing_path, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"Done! Saved to {existing_path}")
