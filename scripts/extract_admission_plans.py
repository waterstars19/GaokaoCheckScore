"""
招生计划数据导入脚本
Extract structured enrollment plan data from all Excel files.
"""
import openpyxl
import json
import os
import re
from datetime import datetime

BASE_DIR = r"D:\GoakaoProject\docs"
DATA_BASE = r"D:\Files\014数据文件夹"
OUTPUT_FILE = os.path.join(BASE_DIR, "admission_plans.json")

os.makedirs(BASE_DIR, exist_ok=True)

all_records = []
sources_processed = []
sources_failed = []

def safe_str(v):
    if v is None:
        return ""
    return str(v).strip()

def safe_int(v):
    try:
        return int(float(str(v).replace("人", "").replace(",", "").strip()))
    except:
        return None

def parse_tuition(v):
    """Parse tuition to integer"""
    s = safe_str(v)
    if not s or s in ('-', '0', '待定'):
        return None
    # Match patterns like "5000元/年", "5000元", "5000"
    m = re.search(r'(\d+\.?\d*)', s.replace(',', ''))
    if m:
        val = float(m.group(1))
        # If it's like "0.5万元", multiply
        if '万' in s:
            val *= 10000
        return int(val)
    return None

def normalize_category(cat):
    """Normalize category to 理科/文科/历史类/物理类"""
    cat = safe_str(cat)
    cat_lower = cat.lower()
    if '理' in cat_lower or '物理' in cat_lower:
        if '文' in cat or '历史' in cat:
            return cat  # mixed
        return '物理类'
    if '文' in cat_lower or '历史' in cat_lower:
        return '历史类'
    return cat

def normalize_batch(batch):
    """Normalize batch name"""
    b = safe_str(batch)
    mapping = {
        '本科第一批': '一本',
        '本科一批': '一本',
        '一本': '一本',
        '本科第二批': '二本',
        '本科二批': '二本',
        '二本': '二本',
        '高职高专批': '专科',
        '高职高专': '专科',
        '专科批': '专科',
        '专科': '专科',
        '高职（专科）批': '专科',
        '国家专项计划批': '国家专项',
        '国家专项': '国家专项',
        '本科提前批': '提前批',
        '提前批': '提前批',
    }
    return mapping.get(b, b)


# ========== Schema B: 招生计划 2017-2022 ==========
print("\n" + "="*60)
print("Processing: 招生计划 2017-2022 (Schema B)")
print("="*60)

plan_dirs_2017_2022 = [
    os.path.join(DATA_BASE, r"2026河南高考志愿填报_参考文档\招生计划\2017-2022"),
    os.path.join(DATA_BASE, r"G25.河南——98数据\河南_招生计划_2017-2022"),
    os.path.join(DATA_BASE, r"13-【井书·独家资料包】河南\河南17-23年\河南_招生计划_2017-2022"),
]

seen_files = set()
for plan_dir in plan_dirs_2017_2022:
    if not os.path.exists(plan_dir):
        print(f"  DIR NOT FOUND: {plan_dir}")
        continue
    for fname in sorted(os.listdir(plan_dir)):
        if not fname.endswith('.xlsx'):
            continue
        fpath = os.path.join(plan_dir, fname)
        # Deduplicate by filename
        if fname in seen_files:
            continue
        seen_files.add(fname)
        print(f"  Reading: {fname} ...", end=" ")
        try:
            wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
            ws = wb[wb.sheetnames[0]]
            # Headers: 年份(1), 学校(2), 省份(3), 城市(4), 软科排名(5), _985(6), _211(7), 双一流(8), 
            # 科类(9), 批次(10), 门类(11), 一级学科(12), 专业(13), 专业代码(14), 招生人数(15), 
            # 学制(16), 学费(17), 办学性质(18), 学校归属(19), 全国统一招生代码(20)
            count = 0
            for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                if not row or not row[0]:
                    continue
                year = safe_int(row[0])
                school = safe_str(row[1])
                major = safe_str(row[12])
                planned = safe_int(row[14])
                code = safe_str(row[13])
                category = normalize_category(safe_str(row[8]))
                batch = normalize_batch(safe_str(row[9]))
                tuition = parse_tuition(str(row[16])) if len(row) > 16 else None
                duration = safe_str(row[15]) if len(row) > 15 else ""
                scode = safe_str(row[19]) if len(row) > 19 else ""
                
                if not year or not school:
                    continue
                
                all_records.append({
                    "year": year,
                    "province": "河南",
                    "category": category,
                    "school": school,
                    "school_code": scode,
                    "major": major,
                    "major_code": code,
                    "batch": batch,
                    "planned_count": planned,
                    "tuition": tuition,
                    "duration": duration,
                    "data_type": "enrollment_plan",
                    "source_file": fname,
                })
                count += 1
            wb.close()
            sources_processed.append(fname)
            print(f"{count} records")
        except Exception as e:
            print(f"FAILED: {e}")
            sources_failed.append((fname, str(e)))


# ========== Schema C: 招生计划 2023 ==========
print("\n" + "="*60)
print("Processing: 招生计划 2023 (Schema C)")
print("="*60)

plan_2023_files = [
    os.path.join(DATA_BASE, r"G25.河南——98数据\河南-2023-招生计划.xlsx"),
    os.path.join(DATA_BASE, r"13-【井书·独家资料包】河南\河南17-23年\河南-2023-招生计划.xlsx"),
]

for fpath in plan_2023_files:
    fname = os.path.basename(fpath)
    if not os.path.exists(fpath):
        print(f"  NOT FOUND: {fpath}")
        continue
    print(f"  Reading: {fname} ...", end=" ")
    try:
        wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
        ws = wb[wb.sheetnames[0]]
        # Headers: 年份(1), 批次(2), 院校代码(3), 院校名称(4), 科类(5), 校计划数(6), 
        # 专业代码(7), 专业名称(8), 学制(9), 计划数(10), 学费(11)
        count = 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or not row[0]:
                continue
            year = safe_int(row[0])
            if not year:
                continue
            all_records.append({
                "year": year,
                "province": "河南",
                "category": normalize_category(safe_str(row[4])),
                "school": safe_str(row[3]),
                "school_code": safe_str(row[2]),
                "major": safe_str(row[7]),
                "major_code": safe_str(row[6]),
                "batch": normalize_batch(safe_str(row[1])),
                "planned_count": safe_int(row[9]),
                "duration": safe_str(row[8]),
                "tuition": parse_tuition(str(row[10])) if len(row) > 10 else None,
                "data_type": "enrollment_plan",
                "source_file": fname,
            })
            count += 1
        wb.close()
        sources_processed.append(fname)
        print(f"{count} records")
    except Exception as e:
        print(f"FAILED: {e}")
        sources_failed.append((fname, str(e)))


# ========== Schema D: 招生计划 2024 ==========
print("\n" + "="*60)
print("Processing: 招生计划 2024 (Schema D)")
print("="*60)

plan_2024_files = [
    os.path.join(DATA_BASE, r"2026河南高考志愿填报_参考文档\招生计划\H河南-招生计划-2024.xlsx"),
    os.path.join(DATA_BASE, r"21-河南高考招生数据-2025最新\河南高考录取数据-2024年\河南-招生计划-2024\H河南-招生计划-2024.xlsx"),
]

for fpath in plan_2024_files:
    fname = os.path.basename(fpath)
    if not os.path.exists(fpath):
        print(f"  NOT FOUND: {fpath}")
        continue
    print(f"  Reading: {fname} ...", end=" ")
    try:
        wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
        ws = wb[wb.sheetnames[0]]
        # Headers: 年份(1), 学校(2), 招生代码(3), 学校方向(4), 省份(5), 科目(6), 计划总数(7),
        # 专业(8), 专业代码(9), 批次(10), 学费(11), 学制(12), 计划人数(13)
        count = 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or not row[0]:
                continue
            year = safe_int(row[0])
            if not year:
                continue
            all_records.append({
                "year": year,
                "province": "河南",
                "category": normalize_category(safe_str(row[5])),
                "school": safe_str(row[1]),
                "school_code": safe_str(row[2]),
                "major": safe_str(row[7]),
                "major_code": safe_str(row[8]),
                "batch": normalize_batch(safe_str(row[9])),
                "planned_count": safe_int(row[12]),
                "duration": safe_str(row[11]),
                "tuition": parse_tuition(str(row[10])) if len(row) > 10 else None,
                "data_type": "enrollment_plan",
                "source_file": fname,
            })
            count += 1
        wb.close()
        sources_processed.append(fname)
        print(f"{count} records")
    except Exception as e:
        print(f"FAILED: {e}")
        sources_failed.append((fname, str(e)))


# ========== Schema E: 招生计划 2025 ==========
print("\n" + "="*60)
print("Processing: 招生计划 2025 (Schema E)")
print("="*60)

plan_2025_files = [
    os.path.join(DATA_BASE, r"2026河南高考志愿填报_参考文档\招生计划\20250621-河南-2025-招生计划.xlsx"),
    os.path.join(DATA_BASE, r"21-河南高考招生数据-2025最新\河南2025招生计划\20250621-河南-2025-招生计划.xlsx"),
]

for fpath in plan_2025_files:
    fname = os.path.basename(fpath)
    if not os.path.exists(fpath):
        print(f"  NOT FOUND: {fpath}")
        continue
    print(f"  Reading: {fname} ...", end=" ")
    try:
        wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
        ws = wb[wb.sheetnames[0]]
        # Headers at row 2: 生源地, 年份, 批次, 科类, 院校代码, 院校名称, 专业组代码,
        # 专业代码, 专业名称, 专业备注, 选科要求, 学制, 学费, 计划人数
        count = 0
        for row in ws.iter_rows(min_row=3, values_only=True):  # data starts at row 3
            if not row or not row[1]:
                continue
            year = safe_int(row[1])
            if not year:
                continue
            all_records.append({
                "year": year,
                "province": "河南",
                "category": normalize_category(safe_str(row[3])),
                "school": safe_str(row[5]),
                "school_code": safe_str(row[4]),
                "major_group_code": safe_str(row[6]),
                "major": safe_str(row[8]),
                "major_code": safe_str(row[7]),
                "major_remark": safe_str(row[9]),
                "subject_requirement": safe_str(row[10]),
                "batch": normalize_batch(safe_str(row[2])),
                "planned_count": safe_int(row[13]),
                "duration": safe_str(row[11]),
                "tuition": parse_tuition(str(row[12])) if len(row) > 12 else None,
                "data_type": "enrollment_plan",
                "source_file": fname,
            })
            count += 1
        wb.close()
        sources_processed.append(fname)
        print(f"{count} records")
    except Exception as e:
        print(f"FAILED: {e}")
        sources_failed.append((fname, str(e)))


# ========== Schema F: 2024年专业录取分数 ==========
print("\n" + "="*60)
print("Processing: 2024年专业录取分数 (Schema F)")
print("="*60)

score_2024_files = [
    os.path.join(DATA_BASE, r"2026河南高考志愿填报_参考文档\录取统计\河南省-2024年专业录取分数.xlsx"),
    os.path.join(DATA_BASE, r"21-河南高考招生数据-2025最新\河南高考录取数据-2024年\河南-专业录取分数线-2024\河南省-2024年专业录取分数.xlsx"),
]

for fpath in score_2024_files:
    fname = os.path.basename(fpath)
    if not os.path.exists(fpath):
        print(f"  NOT FOUND: {fpath}")
        continue
    print(f"  Reading: {fname} ...", end=" ")
    try:
        wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
        # Check both sheets
        for sname in wb.sheetnames:
            ws = wb[sname]
            if ws.max_row and ws.max_row <= 1:
                continue
            count = 0
            # Headers at row 2: 院校代码, 院校名称, 批次, 文理科, 专业代码, 专业名称, 专业备注, 录取人数, 最低分, 最低位次, 最高分
            for row in ws.iter_rows(min_row=3, values_only=True):
                if not row or not row[0]:
                    continue
                school_code = safe_str(row[0])
                if not school_code or school_code.startswith('河南'):
                    continue
                all_records.append({
                    "year": 2024,
                    "province": "河南",
                    "category": normalize_category(safe_str(row[3])),
                    "school": safe_str(row[1]),
                    "school_code": school_code,
                    "major": safe_str(row[5]),
                    "major_code": safe_str(row[4]),
                    "major_remark": safe_str(row[6]),
                    "batch": normalize_batch(safe_str(row[2])),
                    "admitted_count": safe_int(row[7]),
                    "min_score": safe_int(row[8]),
                    "min_rank": safe_int(row[9]),
                    "max_score": safe_int(row[10]),
                    "data_type": "admission_score",
                    "source_file": f"{fname}/{sname}",
                })
                count += 1
            print(f"[{sname}] {count} records ", end="")
        wb.close()
        sources_processed.append(fname)
        print()
    except Exception as e:
        print(f"FAILED: {e}")
        sources_failed.append((fname, str(e)))


# ========== Schema A: 录取统计 2021-2023 (school-level) ==========
print("\n" + "="*60)
print("Processing: 录取统计 (2021-2023, school-level)")
print("="*60)

admit_dir_dirs = [
    os.path.join(DATA_BASE, r"13-【井书·独家资料包】河南\河南全套\24理科录取统计Excel版本"),
    os.path.join(DATA_BASE, r"13-【井书·独家资料包】河南\河南全套\24文科录取统计Excel版本"),
    os.path.join(DATA_BASE, r"2024年河南高考\理科\录取统计"),
    os.path.join(DATA_BASE, r"2024年河南高考\文科\录取统计"),
    os.path.join(DATA_BASE, r"2026河南高考志愿填报_参考文档\录取统计\2024年录取统计\理科"),
    os.path.join(DATA_BASE, r"2026河南高考志愿填报_参考文档\录取统计\2024年录取统计\文科"),
]

for adir in admit_dir_dirs:
    if not os.path.exists(adir):
        continue
    for fname in sorted(os.listdir(adir)):
        if not fname.endswith('.xlsx'):
            continue
        fpath = os.path.join(adir, fname)
        print(f"  Reading: {fname} ...", end=" ")
        try:
            wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
            ws = wb[wb.sheetnames[0]]
            # Headers: 院校代码, 院校名称, 年份, 公布计划, 录取人数, 最高分, 最低分,
            # 最低分与分数线差值, 录取最低分位次, 平均分, 平均分与分数线差值, 科目类别, 批次
            count = 0
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or not row[0]:
                    continue
                year = safe_int(row[2])
                if not year:
                    continue
                all_records.append({
                    "year": year,
                    "province": "河南",
                    "category": normalize_category(safe_str(row[11])),
                    "school": safe_str(row[1]),
                    "school_code": safe_str(row[0]),
                    "batch": normalize_batch(safe_str(row[12])),
                    "planned_count": safe_int(row[3]),
                    "admitted_count": safe_int(row[4]),
                    "max_score": safe_int(row[5]),
                    "min_score": safe_int(row[6]),
                    "score_diff": safe_int(row[7]),
                    "min_rank": safe_int(row[8]),
                    "avg_score": safe_float(row[9]),
                    "avg_diff": safe_float(row[10]),
                    "data_type": "admission_stats_school",
                    "source_file": fname,
                })
                count += 1
            wb.close()
            sources_processed.append(fname)
            print(f"{count} records")
        except Exception as e:
            print(f"FAILED: {e}")
            sources_failed.append((fname, str(e)))

def safe_float(v):
    try:
        return float(str(v))
    except:
        return None


# ========== Write output ==========
print("\n" + "="*60)
print("Writing JSON output...")
print("="*60)

# Gather stats
years = set()
schools = set()
majors = set()
for r in all_records:
    if r.get('year'):
        years.add(r['year'])
    if r.get('school'):
        schools.add(r['school'])
    if r.get('major'):
        majors.add(r['major'])

output = {
    "meta": {
        "version": "1.0",
        "source_count": len(sources_processed),
        "total_records": len(all_records),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "year_range": [min(years), max(years)] if years else [],
        "unique_schools": len(schools),
        "unique_majors": len(majors),
        "records_by_type": {},
        "records_by_year": {},
    },
    "data": all_records,
}

# Count by type
for r in all_records:
    dt = r.get('data_type', 'unknown')
    output["meta"]["records_by_type"][dt] = output["meta"]["records_by_type"].get(dt, 0) + 1
    y = r.get('year', 'unknown')
    output["meta"]["records_by_year"][str(y)] = output["meta"]["records_by_year"].get(str(y), 0) + 1

print(f"\nWriting {len(all_records)} records to {OUTPUT_FILE} ...")
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False)

# Print summary
print("\n" + "="*60)
print("EXTRACTION COMPLETE")
print("="*60)
print(f"Files scanned: {len(sources_processed) + len(sources_failed)}")
print(f"Files processed successfully: {len(sources_processed)}")
print(f"Files failed: {len(sources_failed)}")
if sources_failed:
    for fn, err in sources_failed:
        print(f"  - {fn}: {err}")
print(f"\nTotal records: {len(all_records):,}")
print(f"Year range: {min(years)} - {max(years)}")
print(f"Unique schools: {len(schools):,}")
print(f"Unique majors: {len(majors):,}")
print(f"\nRecords by type:")
for dt, cnt in sorted(output["meta"]["records_by_type"].items()):
    print(f"  {dt}: {cnt:,}")
print(f"\nRecords by year:")
for y, cnt in sorted(output["meta"]["records_by_year"].items()):
    print(f"  {y}: {cnt:,}")
print(f"\nOutput: {OUTPUT_FILE}")
print(f"File size: {os.path.getsize(OUTPUT_FILE) / 1024 / 1024:.1f} MB")
