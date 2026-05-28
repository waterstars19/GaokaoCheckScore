"""
处理全国高校专业详细信息Excel，输出结构化的JSON文件。
"""
import json
import re
import os
import openpyxl

INPUT_FILE = r"D:\Files\014数据文件夹\1647.全国大学院校信息专业介绍数据表\02.全国高校专业对应学习内容介绍（1451个专业）.xlsx"
OUTPUT_FILE = r"D:\GoakaoProject\docs\major_details.json"

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)


def clean_text(val):
    """清理单元格文本：处理_x000D_换行符和多余空白"""
    if val is None:
        return None
    text = str(val).strip()
    # 替换Excel内部的\r\n标记
    text = text.replace("_x000D_\n", "\n")
    text = text.replace("_x000D_", "")
    # 合并多个空白行
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return text if text else None


def strip_json_garbage(text):
    """去除单元格末尾附加的JSON/数组片段垃圾数据
    例如: '...其他地区：42.00%]}、jobrate:[{...' -> '...其他地区：42.00%'
          '...其他：50.80%]、1:[：13.86%...' -> '...其他：50.80%'
    """
    if not text:
        return text
    
    # 模式1: 以 ]} 开头后跟 、jobrate 或类似
    idx = text.find("]}、")
    if idx != -1:
        text = text[:idx]
    
    # 模式2: 以 ]、 开头后跟数字:
    idx = text.find("]、")
    if idx != -1:
        remaining = text[idx+2:]
        # 检查是否像 '1:[：13.86%...' 这样的格式
        if re.match(r'\d+:\[', remaining.strip()):
            text = text[:idx]
    
    # 模式3: 单独残留的 ]}
    idx = text.rfind("]}")
    if idx != -1 and idx > len(text) * 0.5:
        # 只在后半部分发现时才处理
        text = text[:idx]
    
    return text.strip()


def parse_gender_ratio(val):
    """解析性别比例字符串
    '男生：40.00%、女生：60.00%' -> {"male": 40.0, "female": 60.0}
    """
    if not val:
        return None
    text = str(val).strip()
    male_match = re.search(r'男生[：:]\s*([\d.]+)\s*%', text)
    female_match = re.search(r'女生[：:]\s*([\d.]+)\s*%', text)
    if male_match and female_match:
        return {
            "male": round(float(male_match.group(1)), 1),
            "female": round(float(female_match.group(1)), 1)
        }
    return None


def parse_employment_rate(val):
    """解析就业率字符串
    '2015年：70%-75%、2016年：85%-90%、2017年：85%-90%' -> [{"year": 2015, "rate": "70%-75%"}, ...]
    """
    if not val:
        return None
    text = str(val).strip()
    # 匹配模式: YYYY年：XX%-XX%
    pattern = re.compile(r'(\d{4})年[：:]\s*(\d+%-\d+%)')
    matches = pattern.findall(text)
    if matches:
        return [{"year": int(y), "rate": r} for y, r in matches]
    return None


def normalize_major_code(val):
    """规范化专业代码为字符串"""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        s = str(int(val))
        # 补齐前导零到6位
        if len(s) <= 6:
            s = s.zfill(6)
        return s
    s = str(val).strip()
    return s


def process_excel():
    wb = openpyxl.load_workbook(INPUT_FILE, data_only=True)
    ws = wb.active
    
    # 读取表头（第1行）
    headers = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    
    majors = {}
    stats_by_discipline = {}
    total_with_employment = 0
    total_with_gender = 0
    
    for row_idx in range(2, ws.max_row + 1):
        raw = {}
        for col_idx in range(1, ws.max_column + 1):
            raw[headers[col_idx - 1]] = ws.cell(row_idx, col_idx).value
        
        major_name = str(raw.get("专业名称", "")).strip()
        if not major_name:
            continue
        
        discipline = str(raw.get("学科门类", "")).strip() if raw.get("学科门类") else None
        category = str(raw.get("专业类", "")).strip() if raw.get("专业类") else None
        
        # 使用col 3的层次（col 8是重复的）
        level = str(raw.get("层次", "")).strip() if raw.get("层次") else None
        
        duration = str(raw.get("修业年限", "")).strip() if raw.get("修业年限") else None
        degree = str(raw.get("授予学位", "")).strip() if raw.get("授予学位") else None
        subject_suggest = str(raw.get("选考（学科）建议", "")).strip() if raw.get("选考（学科）建议") else None
        
        first_impression = str(raw.get("第一印象", "")).strip() if raw.get("第一印象") else None
        
        # 性别比例
        gender_ratio = parse_gender_ratio(raw.get("性别比例"))
        if gender_ratio:
            total_with_gender += 1
        
        # 就业率
        employment_rate = parse_employment_rate(raw.get("就业率"))
        if employment_rate:
            total_with_employment += 1
        
        # 清理核心文本字段
        description = clean_text(raw.get("专业是什么"))
        courses = clean_text(raw.get("专业学什么"))
        career = clean_text(raw.get("专业干什么"))
        employment_dest = clean_text(raw.get("就业去向"))
        
        # 地区/行业/岗位分布（去除尾部垃圾数据）
        region_dist = clean_text(raw.get("就业地区分布"))
        region_dist = strip_json_garbage(region_dist)
        
        industry_dist = clean_text(raw.get("就业行业分布"))
        industry_dist = strip_json_garbage(industry_dist)
        
        job_dist = clean_text(raw.get("就业岗位分布"))
        job_dist = strip_json_garbage(job_dist)
        
        major_code = normalize_major_code(raw.get("专业代码"))
        
        major_obj = {
            "major_name": major_name,
            "major_code": major_code,
            "discipline": discipline,
            "category": category,
            "level": level,
            "duration": duration,
            "degree": degree,
            "subject_suggest": subject_suggest,
            "first_impression": first_impression,
        }
        
        if gender_ratio:
            major_obj["gender_ratio"] = gender_ratio
        if employment_rate:
            major_obj["employment_rate"] = employment_rate
        if description:
            major_obj["description"] = description
        if courses:
            major_obj["courses"] = courses
        if career:
            major_obj["career"] = career
        if employment_dest:
            major_obj["employment_destinations"] = employment_dest
        if region_dist:
            major_obj["region_distribution"] = region_dist
        if industry_dist:
            major_obj["industry_distribution"] = industry_dist
        if job_dist:
            major_obj["job_distribution"] = job_dist
        
        majors[major_name] = major_obj
        
        # 统计
        if discipline:
            stats_by_discipline[discipline] = stats_by_discipline.get(discipline, 0) + 1
    
    # 编译统计信息
    stats = {
        "total_majors": len(majors),
        "by_discipline": stats_by_discipline,
        "majors_with_employment_rate": total_with_employment,
        "majors_with_gender_ratio": total_with_gender,
        "unique_major_codes": len(set(m["major_code"] for m in majors.values() if m["major_code"])),
        "source_file": os.path.basename(INPUT_FILE),
    }
    
    output = {
        "majors": majors,
        "stats": stats
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"处理完成！")
    print(f"  总专业数: {len(majors)}")
    print(f"  有就业率数据: {total_with_employment}")
    print(f"  有性别比例数据: {total_with_gender}")
    print(f"  学科门类数: {len(stats_by_discipline)}")
    for d, c in sorted(stats_by_discipline.items(), key=lambda x: -x[1]):
        print(f"    {d}: {c}")
    print(f"  输出文件: {OUTPUT_FILE}")
    print(f"  文件大小: {os.path.getsize(OUTPUT_FILE):,} bytes")
    
    return output

if __name__ == "__main__":
    process_excel()
