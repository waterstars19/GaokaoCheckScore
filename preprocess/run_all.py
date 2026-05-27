"""
一键运行全部数据预处理
"""
import os
import sys
import time

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from step1_load_yiduan import compute_yiduan_standards
from step2_load_admission import compute_admission_standards
from step3_load_plan import load_plan
from step4_link_groups import compute_group_standards


def main():
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║     河南高考志愿推荐系统 - 数据预处理       ║")
    print("╚══════════════════════════════════════════════╝")
    print()

    times = {}

    try:
        t0 = time.time()
        compute_yiduan_standards()
        times['第一步：一分一段表标准化'] = time.time() - t0

        t0 = time.time()
        compute_admission_standards()
        times['第二步：录取数据标准化'] = time.time() - t0

        t0 = time.time()
        load_plan()
        times['第三步：招生计划提取'] = time.time() - t0

        t0 = time.time()
        compute_group_standards()
        times['第四步：专业组关联'] = time.time() - t0

        print("=" * 60)
        print("🎉 全部预处理完成！")
        print("=" * 60)
        print(f"\n耗时统计:")
        for step, t in times.items():
            print(f"  {step}: {t:.2f}秒")
        print(f"\n总耗时: {sum(times.values()):.2f}秒")

        # 列出产出文件
        processed_dir = os.path.join(PROJECT_DIR, 'processed')
        print(f"\n产出文件列表 ({processed_dir}):")
        for f in sorted(os.listdir(processed_dir)):
            fpath = os.path.join(processed_dir, f)
            size = os.path.getsize(fpath)
            print(f"  {f:40s} {size/1024:>8.0f} KB")

    except Exception as e:
        print(f"\n❌ 预处理出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
