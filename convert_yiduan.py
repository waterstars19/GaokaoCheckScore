"""
一分一段表归一化脚本
将历年（2017-2025）河南省高考一分一段表统一为 JSON 格式

输出文件: 河南一分一段表_2017-2025.json
"""

import json
import re
import pandas as pd
from pathlib import Path

BASE = Path(r"D:\Files\014数据文件夹\2026河南高考志愿填报_参考文档\一分一段表")
SRC_BASE = Path(r"D:\Files\014数据文件夹")
OUTPUT = Path(r"D:\Files\014数据文件夹\2026河南高考志愿填报_参考文档\河南一分一段表_2017-2025.json")

all_data = []  # 统一存放所有数据行

# ============================================================
# 1. 2025年 新高考 (历史类 + 物理类) — CSV 格式
# ============================================================
print("处理 2025 年数据...")
for cat_key, filename in [
    ("history", "2025河南一分一段_历史类.csv"),
    ("physics", "2025河南一分一段_物理类.csv"),
]:
    df = pd.read_csv(BASE / filename)
    # 字段: 分数,段内人数,累计人数,科目类别,年份,备注
    for _, row in df.iterrows():
        all_data.append({
            "year": 2025,
            "category": cat_key,
            "score": int(row["分数"]),
            "count": int(row["段内人数"]),
            "cumulative": int(row["累计人数"]),
        })
    print(f"  {cat_key}: {len(df)} 行")


# ============================================================
# 2. 2024年 旧高考 (理科 + 文科) — XLSX 格式
# ============================================================
print("处理 2024 年数据...")
for cat_key, filename, sheet in [
    ("physics", "2024年理科一分一段表.xlsx", "Sheet1"),
    ("history", "2024年文科一分一段表.xlsx", "Sheet1"),
]:
    df = pd.read_excel(BASE / filename, sheet_name=sheet, header=1)
    # 字段: 分数, 人数, 累计人数
    cnt = 0
    for _, row in df.iterrows():
        score_str = str(row.iloc[0]).strip()
        count = int(row.iloc[1])
        cumulative = int(row.iloc[2])

        # 处理分数范围行，如 '709-750' 或 '671-750'
        range_match = re.match(r'^(\d+)-(\d+)$', score_str)
        if range_match:
            low, high = int(range_match.group(1)), int(range_match.group(2))
            for s in range(low, high + 1):
                all_data.append({
                    "year": 2024,
                    "category": cat_key,
                    "score": s,
                    "count": 0,  # 区间内具体分布未知，count 置 0
                    "cumulative": cumulative,
                })
                cnt += 1
        else:
            all_data.append({
                "year": 2024,
                "category": cat_key,
                "score": int(score_str),
                "count": count,
                "cumulative": cumulative,
            })
            cnt += 1
    print(f"  {cat_key}: {len(df)} 原始行 → {cnt} 展开行")


# ============================================================
# 3. 2023年 旧高考 (理科 + 文科) — XLSX 格式
# ============================================================
print("处理 2023 年数据...")
df_2023 = pd.read_excel(BASE / "河南-2023-一分一段.xlsx")
# 字段: 省份, 年份, 科目, 批次, 最低位次, 最高位次, 位次区间, 最高分, 最低分, 分数区间, 同分人数
# 科目: 理科/文科 → physics/history
# 只看每个分数段的数据(最低分==最高分的行即为单一分数), 使用同分人数和最低位次
category_map_2023 = {"理科": "physics", "文科": "history"}
for _, row in df_2023.iterrows():
    cat_raw = str(row.iloc[2]).strip()
    cat = category_map_2023.get(cat_raw)
    if cat is None:
        continue
    score = int(row.iloc[7])  # 最高分 (也是最低分，因为一行对应一段)
    count = int(row.iloc[10])  # 同分人数
    # 最低位次 = 该分数段中最小排名
    # 注意: 原始数据最低位次是该分数区间内的最低排名，不是累计排名
    # 但我们用最低位次作为该分数的"最低排名"近似累计
    # 实际上对于志愿填报，"位次"更常用的是累计概念
    # 这里用最低位次作为 cumulative
    cumulative = int(row.iloc[4])  # 最低位次

    # 2023年数据有本科+专科，只保留不重复的最高分记录(取位次最小的)
    # 简单策略: 按分数、科目去重，保留最小cumulative
    all_data.append({
        "year": 2023,
        "category": cat,
        "score": score,
        "count": count,
        "cumulative": cumulative,
    })
print(f"  2023: {len(df_2023)} 原始行 → 已添加")


# ============================================================
# 4. 2017-2022年 旧高考 — XLSX 格式
# ============================================================
print("处理 2017-2022 年数据...")
df_1722 = pd.read_excel(BASE / "河南_一分一段_2022_2017.xlsx")
# 字段: 省份, 年份, 科类, 分数, 段内人数, 累计人数
# 科类: 理科/文科 → physics/history
category_map_1722 = {"理科": "physics", "文科": "history"}
for _, row in df_1722.iterrows():
    year = int(row.iloc[1])
    cat_raw = str(row.iloc[2]).strip()
    cat = category_map_1722.get(cat_raw)
    if cat is None:
        continue
    all_data.append({
        "year": year,
        "category": cat,
        "score": int(row.iloc[3]),
        "count": int(row.iloc[4]),
        "cumulative": int(row.iloc[5]),
    })
print(f"  2017-2022: {len(df_1722)} 行")


# ============================================================
# 5. 输出 JSON
# ============================================================
# 排序: 年份降序, 类别(history在前), 分数降序
category_order = {"history": 0, "physics": 1}
all_data.sort(key=lambda x: (-x["year"], category_order[x["category"]], -x["score"]))

# 2023年去重: 同一(年份, 科目, 分数)取cumulative最小的(即排名最靠前的)
print("去重处理: 2023年数据按 (年份, 科目, 分数) 保留排名最优记录...")

# 用字典收集每个 (year, category, score) 的最小 cumulative，O(n) 一次搞定
best_2023 = {}
for d in all_data:
    if d["year"] == 2023:
        key = (d["year"], d["category"], d["score"])
        if key not in best_2023 or d["cumulative"] < best_2023[key]["cumulative"]:
            best_2023[key] = d

# 构建最终列表：非2023直接保留，2023用去重后的
final_data = [d for d in all_data if d["year"] != 2023]
final_data.extend(best_2023.values())

# 重新排序
final_data.sort(key=lambda x: (-x["year"], category_order[x["category"]], -x["score"]))

output = {
    "meta": {
        "description": "河南省高考一分一段表（2017-2025）",
        "province": "河南",
        "updated": "2026-05-22",
        "categories": {
            "history": "历史类（2025新高考）/ 文科（旧高考）",
            "physics": "物理类（2025新高考）/ 理科（旧高考）"
        },
        "notes": [
            "2025年起河南实行新高考3+1+2模式",
            "2024年分数范围行（如709-750）已展开为逐分数据",
            "2023年数据含本科+专科批次，已去重保留排名最优记录",
            "count=0 表示该分数原始数据为范围段，具体人数未知",
        ],
        "total_records": len(final_data),
        "years": sorted(set(d["year"] for d in final_data), reverse=True),
    },
    "data": final_data,
}

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

# 统计信息
from collections import Counter
year_cat = Counter((d["year"], d["category"]) for d in final_data)
print(f"\n{'='*60}")
print(f"输出文件: {OUTPUT}")
print(f"总记录数: {len(final_data)}")
print(f"\n各年份-科目记录数:")
for (y, c), n in sorted(year_cat.items(), reverse=True):
    print(f"  {y} {c}: {n} 条")
print(f"\n文件大小: {OUTPUT.stat().st_size / 1024:.0f} KB")
print("完成!")
