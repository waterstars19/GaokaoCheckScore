"""
Fix and re-extract admission stats (Schema A) files that failed.
Also adds deduplication.
"""
import openpyxl
import json
import os
import re
from datetime import datetime

BASE_DIR = r"D:\GoakaoProject\docs"
DATA_BASE = r"D:\Files\014数据文件夹"
INPUT_FILE = os.path.join(BASE_DIR, "admission_plans.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "admission_plans_v2.json")

# Load existing records
print("Loading existing records...")
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    existing = json.load(f)

all_records = existing.get('data', [])
print(f"Loaded {len(all_records):,} existing records")

new_sources = []
new_failed = []

def safe_str(v):
    if v is None:
        return ""
    return str(v).strip()

def safe_int(v):
    try:
        return int(float(str(v).replace("人", "").replace(",", "").strip()))
    except:
        return None

def safe_float(v):
    try:
        return float(str(v))
    except:
        return None

def parse_tuition(v):
    s = safe_str(v)
    if not s or s in ('-', '0', '待定'):
        return None
    m = re.search(r'(\d+\.?\d*)', s.replace(',', ''))
    if m:
        val = float(m.group(1))
        if '万' in s:
            val *= 10000
        return int(val)
    return None

def normalize_category(cat):
    cat = safe_str(cat)
    cat_lower = cat.lower()
    if '理' in cat_lower or '物理' in cat_lower:
        return '物理类'
    if '文' in cat_lower or '历史' in cat_lower:
        return '历史类'
    return cat

def normalize_batch(batch):
    b = safe_str(batch)
    mapping = {
        '本科第一批': '一本', '本科一批': '一本', '一本': '一本',
        '本科第二批': '二本', '本科二批': '二本', '二本': '二本',
        '高职高专批': '专科', '高职高专': '专科', '专科批': '专科', '专科': '专科',
        '高职（专科）批': '专科',
        '国家专项计划批': '国家专项', '国家专项': '国家专项',
        '本科提前批': '提前批', '提前批': '提前批',
    }
    return mapping.get(b, b)


# ========== Re-process Schema A: 录取统计 ==========
print("\n" + "="*60)
print("Re-processing: 录取统计 (2021-2023, school-level)")
print("="*60)

admit_dirs = [
    os.path.join(DATA_BASE, r"13-【井书·独家资料包】河南\河南全套\24理科录取统计Excel版本"),
    os.path.join(DATA_BASE, r"13-【井书·独家资料包】河南\河南全套\24文科录取统计Excel版本"),
    os.path.join(DATA_BASE, r"2024年河南高考\理科\录取统计"),
    os.path.join(DATA_BASE, r"2024年河南高考\文科\录取统计"),
    os.path.join(DATA_BASE, r"2026河南高考志愿填报_参考文档\录取统计\2024年录取统计\理科"),
    os.path.join(DATA_BASE, r"2026河南高考志愿填报_参考文档\录取统计\2024年录取统计\文科"),
]

seen = set()
for adir in admit_dirs:
    if not os.path.exists(adir):
        continue
    for fname in sorted(os.listdir(adir)):
        if not fname.endswith('.xlsx'):
            continue
        # Skip already-processed duplicates
        fpath = os.path.join(adir, fname)
        fsize = os.path.getsize(fpath)
        key = f"{fname}_{fsize}"
        if key in seen:
            continue
        seen.add(key)
        
        print(f"  Reading: {fname} ({fsize/1024:.0f}KB) ...", end=" ")
        
        # Check if file is valid zip/xlsx
        try:
            wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
        except Exception as e:
            print(f"SKIPPED (not valid xlsx): {e}")
            new_failed.append((fname, f"not valid xlsx: {e}"))
            continue
        
        try:
            ws = wb[wb.sheetnames[0]]
            # Headers: 院校代码(1), 院校名称(2), 年份(3), 公布计划(4), 录取人数(5), 
            # 最高分(6), 最低分(7), 最低分与分数线差值(8), 录取最低分位次(9), 
            # 平均分(10), 平均分与分数线差值(11), 科目类别(12), 批次(13)
            count = 0
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or not row[0]:
                    continue
                try:
                    if len(row) < 13:
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
                except:
                    continue
            wb.close()
            new_sources.append(fname)
            print(f"{count} records")
        except Exception as e:
            print(f"FAILED: {e}")
            new_failed.append((fname, str(e)))


# ========== Deduplicate ==========
print("\n" + "="*60)
print("Deduplicating...")
print("="*60)

# Build a set of unique keys: (year, school_code, school, major, major_code, batch, category, data_type)
seen_keys = set()
deduped = []
dup_count = 0
for r in all_records:
    key = (
        r.get('year'), r.get('school_code'), r.get('school'),
        r.get('major'), r.get('major_code'), r.get('batch'),
        r.get('category'), r.get('data_type', 'enrollment_plan'),
        r.get('planned_count'), r.get('admitted_count'),
    )
    if key in seen_keys:
        dup_count += 1
        continue
    seen_keys.add(key)
    deduped.append(r)

print(f"Removed {dup_count:,} duplicates")
print(f"Records: {len(deduped):,}")


# ========== Stats ==========
years = set()
schools = set()
majors = set()
for r in deduped:
    if r.get('year'):
        years.add(r['year'])
    if r.get('school'):
        schools.add(r['school'])
    if r.get('major'):
        majors.add(r['major'])

records_by_type = {}
records_by_year = {}
for r in deduped:
    dt = r.get('data_type', 'unknown')
    records_by_type[dt] = records_by_type.get(dt, 0) + 1
    y = r.get('year', 'unknown')
    records_by_year[str(y)] = records_by_year.get(str(y), 0) + 1


# ========== Write output ==========
print("\n" + "="*60)
print("Writing final JSON...")
print("="*60)

output = {
    "meta": {
        "version": "2.0",
        "source_files_processed": len(new_sources) + 10,
        "sources_failed": len(new_failed),
        "total_records": len(deduped),
        "duplicates_removed": dup_count,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "year_range": [min(years), max(years)] if years else [],
        "unique_schools": len(schools),
        "unique_majors": len(majors),
        "records_by_type": records_by_type,
        "records_by_year": records_by_year,
    },
    "data": deduped,
}

# Sort by year, school
deduped.sort(key=lambda r: (r.get('year', 0), r.get('school', ''), r.get('major', '')))

print(f"Writing {len(deduped):,} records to {OUTPUT_FILE} ...")
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False)

# ========== Print summary ==========
print("\n" + "="*60)
print("FINAL REPORT")
print("="*60)
print(f"Total records: {len(deduped):,}")
print(f"Year range: {min(years)} - {max(years)}")
print(f"Unique schools: {len(schools):,}")
print(f"Unique majors: {len(majors):,}")
print(f"\nRecords by type:")
for dt, cnt in sorted(records_by_type.items()):
    print(f"  {dt}: {cnt:,}")
print(f"\nRecords by year:")
for y, cnt in sorted(records_by_year.items()):
    print(f"  {y}: {cnt:,}")
if new_failed:
    print(f"\nFailed files ({len(new_failed)}):")
    for fn, err in new_failed:
        print(f"  - {fn}: {err}")
print(f"\nOutput: {OUTPUT_FILE}")
print(f"File size: {os.path.getsize(OUTPUT_FILE) / 1024 / 1024:.1f} MB")
