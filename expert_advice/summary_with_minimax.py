"""使用 MiniMax-M2.7-highspeed 处理转写数据"""
import json
import subprocess
import sys

data_path = r'D:\GoakaoProject\expert_advice\bilibili_videos\all_transcripts.json'
with open(data_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f'共 {len(data)} 个视频')

system_prompt = (
    '你是一个高考志愿填报专家分析工具。请将以下张雪峰视频的原始语音转写文本，'
    '处理成结构化的专家意见数据。\n\n'
    '要求：\n'
    '1. 去掉所有口语化表达（呃、那个、就是说、然后、那啥等语气词和重复）\n'
    '2. 保留核心观点和具体数据/建议\n'
    '3. 每条专家意见要有：观点核心 + 具体说明\n'
    '4. 标注关键词标签\n'
    '5. 输出格式为纯 JSON（不要额外说明文字），结构如下：\n'
    '{\n'
    '  "video_title": "视频标题",\n'
    '  "video_url": "URL",\n'
    '  "duration_seconds": 整数,\n'
    '  "topics": ["话题1"],\n'
    '  "keywords": ["关键词1"],\n'
    '  "expert_opinions": [\n'
    '    { "point": "观点核心一句话", "detail": "具体说明", "tags": ["标签"] }\n'
    '  ],\n'
    '  "actionable_advice": ["可直接执行的建议"]\n'
    '}\n\n'
    '注意：只输出纯 JSON，不要有任何额外的说明文字。'
)

results = []

for i, v in enumerate(data):
    title = v['title']
    text = v['full_text']
    print(f'[{i+1}/{len(data)}] {title} ({len(text)}字符)...')
    
    user_msg = (
        f'视频标题: {title}\n'
        f'视频时长: {v["duration"]}秒\n'
        f'URL: {v["url"]}\n\n'
        f'转写全文:\n{text}'
    )
    
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_msg}
    ]
    
    msg_file = r'D:\GoakaoProject\expert_advice\bilibili_videos\mmx_msg.json'
    with open(msg_file, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False)
    
    cmd = 'mmx text chat --model MiniMax-M2.7-highspeed --messages-file "' + msg_file + '" --output json --quiet --non-interactive --max-tokens 4096 --temperature 0.3'
    
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, encoding='utf-8', shell=True)
    
    if proc.returncode == 0:
        stdout = proc.stdout.strip()
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            parsed = {'content': stdout}
        
        content = ''
        if isinstance(parsed, dict):
            for key in ['content', 'response', 'text']:
                if key in parsed and parsed[key]:
                    content = parsed[key]
                    break
            if not content and 'choices' in parsed:
                try:
                    content = parsed['choices'][0]['message']['content']
                except (KeyError, IndexError, TypeError):
                    pass
            if not content:
                content = str(parsed)
        else:
            content = str(parsed)
        
        # 尝试提取 JSON（可能被包裹在 markdown 代码块中）
        content = content.strip()
        if '```' in content:
            import re
            m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
            if m:
                content = m.group(1).strip()
        
        # 尝试多种方式解析
        rj = None
        
        # 方式1: 标准 JSON
        try:
            rj = json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # 方式2: Python dict (单引号)
        if rj is None:
            try:
                import ast
                rj = ast.literal_eval(content)
            except (SyntaxError, ValueError):
                pass
        
        # 方式3: 替换单引号为双引号
        if rj is None:
            try:
                # 先把 True/False/None 转成 JSON 格式
                fixed = content.replace("'", '"')
                fixed = fixed.replace('True', 'true').replace('False', 'false').replace('None', 'null')
                rj = json.loads(fixed)
            except json.JSONDecodeError:
                pass
        
        if rj is not None:
            results.append(rj)
            opinions = rj.get('expert_opinions', [])
            keywords = rj.get('keywords', [])
            print(f'  OK - {len(opinions)}条意见, {len(keywords)}个关键词')
        else:
            print(f'  解析失败, 输出: {content[:300]}')
            results.append({
                'video_title': title,
                'video_url': v['url'],
                'raw_content': content[:2000]
            })
    else:
        print(f'  FAIL: {proc.stderr[:200]}')
        results.append({
            'video_title': title,
            'video_url': v['url'],
            'error': proc.stderr[:500]
        })

# 写入结果
out = {
    'source': 'B站张雪峰高考志愿指导视频',
    'transcribe_engine': 'FunASR Paraformer',
    'summary_engine': 'MiniMax-M2.7-highspeed',
    'total_videos': len(data),
    'videos': results
}

out_path = r'D:\GoakaoProject\expert_advice\bilibili_videos\expert_summary.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

success = sum(1 for r in results if 'error' not in r)
print(f'\n完成! 保存到 {out_path}')
print(f'成功: {success}/{len(results)}')
