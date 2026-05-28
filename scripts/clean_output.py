# -*- coding: utf-8 -*-
"""Clean the college data by removing obviously noisy entries."""
import json

with open('D:/GoakaoProject/data_985/985_schools_local.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

noise_starters = [
    '与交大', '依托', '全体', '合性', '名中', '推动', '新组建', '是由',
    '标志着', '的上海', '的交大', '而成', '与渥', '震旦',
    '基础上', '定名', '改为', '原名', '原', '年',
    '个科教', '个全日制', '个管理型', '个教学',
    '庆大学', '括海洋', '接管理', '工大学莱斯特', '连凌水',
    '努力', '包括', '化实施', '实施', '和的',
    '为之', '的国', '在多次', '多所', '重点', '嘉及',
    '为建成', '合并', '成立', '成绩', '最早', '现设',
    '研指标', '的国立',
    '在东北', '和理学',
    '合并', '为基础',
    '设立', '资队伍',
    '迎来', '挂靠', '我们回顾', '受文化部', '名为', '并入',
    '术科学', '管理干', '兼任', '举行',
    '学院下', '董晨教授',
    '的和',
    '南极', '两国',
    '和华北', '立北京', '校内设',
    '由北京', '方面', '中的',
    '亚昆士兰', '所孔子', '的孔子', '布拉迪', '法国尼斯', '立北平',
    '西安筹', '在美', '在华', '伦敦', '瑞典', '雷恩', '加拿大',
    '在美国', '国马里兰', '以钱学',
    '到了', '现在',
    '二级学院', '专业学院', '个专业学院', '所独立学院',
    '个学科', '个国际化',
    '基础', '发展',
    '海外教育学院等',
    '以及成',
]

noise_contains = [
    '孔子学院', '继续教育', '网络教育', '远程教育',
    '伦敦大学', '瑞典皇家', '雷恩一大',
    '哈佛大学医学院',
    '科技大学', '工业学院', '工学院',
    '军事医学',
    '理工学院',
    '研究院',
]

def is_good_college(name):
    if len(name) < 5:
        return False
    for s in noise_starters:
        if name.startswith(s):
            return False
    for c in noise_contains:
        if c in name:
            return False
    return True

for s in data['schools']:
    s['college_list'] = [c for c in s['college_list'] if is_good_college(c)]

with open('D:/GoakaoProject/data_985/985_schools_local.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Print summary
total_colleges = sum(len(s['college_list']) for s in data['schools'])
col_schools = sum(1 for s in data['schools'] if s['college_list'])
print(f'Cleaned: {col_schools} schools have colleges ({total_colleges} total)')
print()
for s in data['schools']:
    if s['college_list']:
        print(f'  {s["school_name"]}: {s["college_list"]}')
