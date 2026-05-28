import json

with open(r"D:\GoakaoProject\expert_advice\batch5\expert_summary.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("=" * 70)
print("BATCH 5 - 张雪峰视频分析总结")
print("=" * 70)

total_opinions = 0
total_keywords = 0
total_topics = 0

for i, v in enumerate(data["videos"]):
    title = v.get("video_title", v.get("file", "unknown"))
    dur = v.get("duration_seconds", "?")
    opinions = v.get("expert_opinions", [])
    keywords = v.get("keywords", [])
    topics = v.get("topics", [])
    total_opinions += len(opinions)
    total_keywords += len(keywords)
    total_topics += len(topics)

    print(f"\n📹 #{i+1} {title}")
    print(f"   时长: {dur}s | 观点: {len(opinions)}条 | 关键词: {len(keywords)}个 | 话题: {len(topics)}个")
    if topics:
        print(f"   话题: {', '.join(topics)}")
    kwords = ", ".join(keywords[:8])
    if len(keywords) > 8:
        kwords += "..."
    print(f"   关键词: {kwords}")

    for j, op in enumerate(opinions, 1):
        point = op.get("point", "?")
        print(f"   观点{j}: {point}")
        detail = op.get("detail", "")
        if detail:
            d = detail[:100]
            if len(detail) > 100:
                d += "..."
            print(f"        {d}")

    advice = v.get("actionable_advice", [])
    if advice:
        print("   建议:")
        for a in advice:
            if isinstance(a, str):
                print(f"       • {a[:100]}")
            elif isinstance(a, dict):
                txt = a.get("advice", str(a))[:100]
                print(f"       • {txt}")

print(f"\n{'='*70}")
print(f"📊 总计: {len(data['videos'])} 个视频 | {total_opinions} 条专家观点 | {total_keywords} 个关键词 | {total_topics} 个话题")
print("=" * 70)
