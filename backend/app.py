"""
高考志愿推荐系统 v3 - 支持专业级推荐 + 省份/专业类别/选科筛选
"""
import json, os, math, re
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(PROJECT_DIR, 'processed')
FRONTEND_DIR = os.path.join(PROJECT_DIR, 'frontend')

# ========== 全局数据 ==========
STANDARDIZED = {}
MAJOR_STD = {}       # (year, school, major) → {low_std, high_std}
SCHOOL_STD = {}       # (year, school, category) → {low_std, high_std}
GROUP_STD = {}        # (school, group_code, cat) → {...}
GROUP_MAJORS = {}     # (school, group_code, cat) → [...]
TOTAL_COUNTS = {}
SCHOOL_PROVINCE = {}  # school → province
MAJOR_CATEGORY = {}   # (school, major) → category string

CAT_MAP = {
    '理科': 'physics', '物理': 'physics', '物理类': 'physics',
    '文科': 'history', '历史': 'history', '历史类': 'history',
}
CAT_REVERSE = {'physics': '物理', 'history': '历史'}

# ========== 省份映射（学校名 → 省份）==========
PROVINCES = [
    '北京', '天津', '上海', '重庆',
    '河北', '山西', '辽宁', '吉林', '黑龙江',
    '江苏', '浙江', '安徽', '福建', '江西', '山东',
    '河南', '湖北', '湖南', '广东', '海南',
    '四川', '贵州', '云南', '陕西', '甘肃', '青海',
    '内蒙古', '广西', '西藏', '宁夏', '新疆',
]

CITY_TO_PROV = {
    '郑州': '河南', '洛阳': '河南', '开封': '河南', '新乡': '河南', '南阳': '河南',
    '信阳': '河南', '安阳': '河南', '平顶山': '河南', '许昌': '河南', '焦作': '河南',
    '周口': '河南', '商丘': '河南', '驻马店': '河南', '漯河': '河南', '濮阳': '河南',
    '鹤壁': '河南', '三门峡': '河南', '济源': '河南',
    '北京': '北京', '上海': '上海', '天津': '天津', '重庆': '重庆',
    '哈尔滨': '黑龙江', '大庆': '黑龙江', '齐齐哈尔': '黑龙江',
    '长春': '吉林', '吉林': '吉林', '延边': '吉林',
    '沈阳': '辽宁', '大连': '辽宁', '鞍山': '辽宁', '锦州': '辽宁', '抚顺': '辽宁',
    '石家庄': '河北', '唐山': '河北', '保定': '河北', '秦皇岛': '河北', '邯郸': '河北',
    '太原': '山西', '大同': '山西',
    '济南': '山东', '青岛': '山东', '烟台': '山东', '威海': '山东', '潍坊': '山东',
    '临沂': '山东', '曲阜': '山东', '淄博': '山东', '聊城': '山东', '日照': '山东',
    '南京': '江苏', '苏州': '江苏', '无锡': '江苏', '常州': '江苏', '镇江': '江苏',
    '南通': '江苏', '徐州': '江苏', '扬州': '江苏', '盐城': '江苏', '淮安': '江苏',
    '连云港': '江苏', '泰州': '江苏', '宿迁': '江苏',
    '杭州': '浙江', '宁波': '浙江', '温州': '浙江', '嘉兴': '浙江', '绍兴': '浙江',
    '金华': '浙江', '台州': '浙江', '湖州': '浙江', '丽水': '浙江', '舟山': '浙江',
    '合肥': '安徽', '芜湖': '安徽', '蚌埠': '安徽', '安庆': '安徽', '马鞍山': '安徽',
    '淮北': '安徽', '阜阳': '安徽', '淮南': '安徽', '滁州': '安徽', '铜陵': '安徽',
    '福州': '福建', '厦门': '福建', '泉州': '福建', '漳州': '福建', '龙岩': '福建',
    '三明': '福建', '武夷': '福建',
    '南昌': '江西', '赣州': '江西', '景德镇': '江西', '九江': '江西', '宜春': '江西',
    '吉安': '江西', '上饶': '江西', '抚州': '江西',
    '武汉': '湖北', '宜昌': '湖北', '荆州': '湖北', '襄阳': '湖北', '黄石': '湖北',
    '十堰': '湖北', '荆门': '湖北', '孝感': '湖北', '恩施': '湖北', '咸宁': '湖北',
    '长沙': '湖南', '湘潭': '湖南', '衡阳': '湖南', '株洲': '湖南', '岳阳': '湖南',
    '常德': '湖南', '益阳': '湖南', '邵阳': '湖南', '永州': '湖南', '怀化': '湖南',
    '湘西': '湖南', '郴州': '湖南', '娄底': '湖南',
    '广州': '广东', '深圳': '广东', '珠海': '广东', '东莞': '广东', '佛山': '广东',
    '中山': '广东', '汕头': '广东', '惠州': '广东', '韶关': '广东', '肇庆': '广东',
    '江门': '广东', '茂名': '广东', '梅州': '广东', '湛江': '广东', '清远': '广东',
    '南宁': '广西', '桂林': '广西', '柳州': '广西', '北海': '广西', '百色': '广西',
    '玉林': '广西',
    '海口': '海南', '三亚': '海南',
    '成都': '四川', '绵阳': '四川', '乐山': '四川', '泸州': '四川', '宜宾': '四川',
    '南充': '四川', '自贡': '四川', '攀枝花': '四川',
    '贵阳': '贵州', '遵义': '贵州', '凯里': '贵州', '黔南': '贵州', '黔东南': '贵州',
    '昆明': '云南', '大理': '云南', '曲靖': '云南', '玉溪': '云南', '红河': '云南',
    '西安': '陕西', '咸阳': '陕西', '宝鸡': '陕西', '延安': '陕西', '汉中': '陕西',
    '兰州': '甘肃', '天水': '甘肃', '张掖': '甘肃', '陇南': '甘肃',
    '西宁': '青海',
    '银川': '宁夏', '石嘴山': '宁夏',
    '乌鲁木齐': '新疆', '石河子': '新疆', '克拉玛依': '新疆', '喀什': '新疆',
    '阿克苏': '新疆', '伊犁': '新疆', '阿拉尔': '新疆', '塔里木': '新疆',
    '呼和浩特': '内蒙古', '包头': '内蒙古', '赤峰': '内蒙古', '通辽': '内蒙古',
    '呼伦贝尔': '内蒙古',
    '拉萨': '西藏',
    '香港': '香港', '澳门': '澳门',
}

# 特殊学校名 → 省份
SPECIAL_SCHOOL_PROV = {
    '南开大学': '天津', '华侨大学': '福建', '仰恩大学': '福建',
    '西湖大学': '浙江', '南方科技大学': '广东', '南方医科大学': '广东',
    '深圳大学': '广东', '深圳技术大学': '广东',
    '中国农业大学': '北京', '中国政法大学': '北京', '中国传媒大学': '北京',
    '中国石油大学(北京)': '北京', '中国矿业大学(北京)': '北京',
    '中国石油大学(华东)': '山东', '中国矿业大学': '江苏',
    '中国地质大学(武汉)': '湖北', '中国地质大学(北京)': '北京',
    '中国医科大学': '辽宁', '中国药科大学': '江苏',
    '中国民航大学': '天津', '中国民用航空飞行学院': '四川',
    '中国科学院大学': '北京', '中国社会科学院大学': '北京',
    '中央民族大学': '北京', '中央财经大学': '北京', '中央美术学院': '北京',
    '华北电力大学': '北京', '华北水利水电大学': '河南',
    '东北大学': '辽宁', '东北师范大学': '吉林', '东北林业大学': '黑龙江',
    '东北石油大学': '黑龙江', '东北财经大学': '辽宁', '东北电力大学': '吉林',
    '西北大学': '陕西', '西北工业大学': '陕西', '西北农林科技大学': '陕西',
    '西北政法大学': '陕西', '西北师范大学': '甘肃', '西北民族大学': '甘肃',
    '西南大学': '重庆', '西南政法大学': '重庆', '西南交通大学': '四川',
    '西南财经大学': '四川', '西南科技大学': '四川', '西南民族大学': '四川',
    '西南医科大学': '四川', '西南石油大学': '四川',
    '东南大学': '江苏', '东华大学': '上海', '东华理工大学': '江西',
    '中南大学': '湖南', '中南财经政法大学': '湖北', '中南林业科技大学': '湖南',
    '华东师范大学': '上海', '华东理工大学': '上海', '华东政法大学': '上海',
    '华东交通大学': '江西',
    '华南理工大学': '广东', '华南农业大学': '广东', '华南师范大学': '广东',
    '华西': '四川',
    '上海': '上海', '北京': '北京', '天津': '天津', '重庆': '重庆',
    '广东': '广东', '深圳': '广东', '广州': '广东',
}

# ========== 专业类别关键词映射 ==========
MAJOR_CATEGORIES = {
    '计算机/电子信息': ['计算机', '软件', '数据科学', '大数据', '人工智能', '智能',
                       '电子', '信息', '通信', '网络', '物联网', '自动化', '机器人',
                       '光电', '微电子', '集成电路', '数字媒体技术', '信息安全'],
    '医学/药学': ['医学', '临床', '药学', '护理', '口腔', '中医', '中药', '康复',
                  '检验', '影像', '麻醉', '预防医学', '中西医', '针灸', '眼视光',
                  '医学技术', '口腔医学', '护理学', '法医学', '精神医学', '儿科学'],
    '经济/管理': ['经济', '金融', '保险', '投资', '管理', '会计', '审计', '财务',
                  '市场', '营销', '国贸', '工商', '旅游', '酒店', '物流', '电商',
                  '人力资源', '行政管理', '公共管理', '农林经济', '财政', '税务'],
    '法学/政治': ['法学', '法律', '知识产权', '政治', '社会学', '社会工作',
                  '民族学', '人类学', '国际关系', '外交', '行政管理', '马克思主义'],
    '文学/传媒': ['文学', '语言', '新闻', '传播', '广告', '翻译', '英语', '日语',
                  '俄语', '法语', '德语', '西班牙语', '汉语', '编辑', '出版',
                  '广播电视', '播音', '编导', '汉语言'],
    '理学': ['数学', '应用数学', '物理', '应用物理', '化学', '应用化学',
             '生物科学', '生物技术', '统计学', '应用统计', '地理科学',
             '海洋科学', '大气科学', '地球物理', '心理学', '材料化学'],
    '工学': ['机械', '土木', '建筑', '材料', '材料科学与工程', '化工', '环境',
             '能源', '动力', '交通', '测绘', '水利', '安全', '地质', '矿业',
             '纺织', '轻工', '食品', '航空航天', '兵器', '核工程', '冶金',
             '车辆', '船舶', '飞行', '包装', '印刷'],
    '农学': ['农学', '园艺', '植物', '动物', '林学', '水产', '草业', '茶学',
             '蚕学', '种子', '农业', '兽医', '植保', '森保', '设施农业'],
    '艺术/体育': ['艺术', '美术', '设计', '音乐', '舞蹈', '体育', '运动',
                  '表演', '绘画', '雕塑', '书法', '动画', '视觉传达',
                  '环境设计', '服装', '产品设计', '工艺', '数字媒体艺术'],
    '教育/师范': ['教育', '师范', '小学', '学前', '幼教', '特殊教育',
                  '教育学', '教育技术', '科学教育', '人文教育'],
}

ALL_CATEGORIES = list(MAJOR_CATEGORIES.keys())


def _detect_province(school):
    """从学校名称检测所在省份"""
    if school in SPECIAL_SCHOOL_PROV:
        return SPECIAL_SCHOOL_PROV[school]
    # 检查是否以省份名开头
    for p in sorted(PROVINCES, key=len, reverse=True):
        if school.startswith(p):
            return p
    # 检查是否以城市名开头
    for city, prov in sorted(CITY_TO_PROV.items(), key=lambda x: -len(x[0])):
        if school.startswith(city):
            return prov
    return '其他'


def _detect_major_category(major_name):
    """从专业名称检测所属类别"""
    for cat, kws in MAJOR_CATEGORIES.items():
        for kw in kws:
            if kw in major_name:
                return cat
    return '其他'


# ========== 专业标签（数据驱动 + 知识补充）==========

# 专业大类映射（用于热度分析和标签展示）
MAJOR_GROUP_KEYWORDS = [
    ('计算机/软件', ['计算机', '软件', '大数据', '人工智能', '智能', '网络', '信息安全']),
    ('电子/通信', ['电子', '通信', '电气', '光电', '微电子', '电信']),
    ('集成电路', ['集成电路', '芯片']),
    ('机械/制造', ['机械', '机器人', '车辆', '仪器', '自动化']),
    ('土木/建筑', ['土木', '建筑', '水利', '测绘', '城乡规划']),
    ('医学', ['临床', '口腔', '护理', '药学', '医', '麻醉', '眼视光']),
    ('法学', ['法学', '法律']),
    ('金融/经济', ['金融', '经济', '财政', '国际贸易', '税收']),
    ('会计/财管', ['会计', '财务', '审计', '财管']),
    ('汉语言/思政', ['汉语言', '思想政治', '马克思', '哲学', '中文']),
    ('师范/教育', ['师范', '教育', '小学', '学前', '教技']),
    ('管理', ['管理', '工商', '市场', '人力']),
    ('新闻/传播', ['新闻', '传播', '广告', '播音']),
    ('艺术/设计', ['美术', '设计', '音乐', '舞蹈', '表演', '艺术']),
    ('体育', ['体育']),
    ('农学/食品', ['农学', '食品', '畜牧', '兽医', '园艺']),
    ('生物/化学/环境', ['生物', '化学', '环境', '材料', '生工']),
]

# 分层热度标签（基于实际录取数据的分析结果）
# 同层次内按平均标准分排序：前25%🔥🔥, 25-50%🔥, 50-75%❄️, 后25%❄️❄️
TIER_HOT_LABELS = {
    'high': {  # 985/211层次（标准化分≥500k）
        '艺术/设计': '🔥🔥', '金融/经济': '🔥🔥',
        '会计/财管': '🔥', '土木/建筑': '🔥', '法学': '🔥',
        '机械/制造': '❄️', '医学': '❄️', '电子/通信': '❄️',
        '计算机/软件': '❄️❄️', '汉语言/思政': '❄️❄️', '师范/教育': '❄️❄️',
    },
    'mid': {  # 一本/二本层次（200k ~ 500k）
        '法学': '🔥🔥', '金融/经济': '🔥🔥',
        '汉语言/思政': '🔥', '会计/财管': '🔥', '医学': '🔥',
        '计算机/软件': '❄️', '师范/教育': '❄️', '艺术/设计': '❄️',
        '电子/通信': '❄️❄️', '土木/建筑': '❄️❄️', '机械/制造': '❄️❄️',
    },
    'low': {  # 专科层次（<200k）
        '法学': '🔥🔥', '汉语言/思政': '🔥🔥',
        '金融/经济': '🔥', '师范/教育': '🔥', '医学': '🔥',
        '会计/财管': '❄️', '机械/制造': '❄️', '电子/通信': '❄️',
        '土木/建筑': '❄️❄️', '艺术/设计': '❄️❄️', '计算机/软件': '❄️❄️',
    }
}

# 专业核心特征标签（不依赖分数，基于专业本质属性）
MAJOR_FEATURE_TAGS = {
    '计算机|软件|人工智能|大数据|智能': ['💻 高薪技术'],
    '电子|通信|电气|自动化|光电|微电子': ['🔧 工科技术'],
    '机械|机器人|车辆|仪器': ['🏭 制造产业'],
    '土木|建筑|水利|测绘': ['🏗️ 基建行业'],
    '临床|口腔|麻醉': ['🏥 临床医学'],
    '护理|药学': ['💊 医疗健康'],
    '法学|法律': ['⚖️ 法律专业'],
    '金融|经济|财政|国贸|税收': ['💰 经管金融'],
    '会计|财务|审计': ['📊 财务专业'],
    '汉语言|中文|哲学': ['📚 人文社科'],
    '思想政治|马克思': ['🎯 思政教育'],
    '师范|小学|学前|教技': ['📖 教师职业'],
    '管理|工商|市场': ['🏢 管理学科'],
    '新闻|传播|广告|播音': ['📺 传媒专业'],
    '美术|设计|艺术|音乐|舞蹈|表演': ['🎨 艺术专业'],
    '体育': ['⚽ 体育专业'],
    '农学|食品|畜牧|兽医|园艺': ['🌾 农林食品'],
    '生物|化学|环境|材料': ['🔬 基础科学'],
}
# 标签说明（用于浮窗展示）
TAG_DESCRIPTIONS = {
    '高薪技术': '💻 含计算机科学与技术、软件工程、人工智能、信息安全等专业，是当前起薪最高的大类专业，应届生起薪普遍8000-15000元，资深工程师年薪可达30-50万。就业覆盖互联网大厂、金融科技、政府信息化等几乎所有行业。适合数学逻辑好、动手能力强、能持续学习新技术的理科生。热门方向如人工智能、信息安全前景最好但学习难度大。需注意：技术迭代快，存在35岁职场瓶颈争议，普通院校毕业生需靠项目经验和实习弥补学历差距，不能只靠课堂教学。',
    '工科技术': '🔧 含电子信息工程、通信工程、自动化、微电子等专业，是5G和新基建时代核心工科。毕业生可进入华为/中兴等通信设备商、三大运营商、芯片设计企业等，应届生起薪6000-12000元，薪酬成长性好。行业不像互联网那样内卷，硬件研发领域资深专家依然吃香。适合物理成绩好、喜欢动手实践的理科生。需注意：学习难度大挂科率高；芯片设计等高端方向建议读研。从二本到985均有对应院校可选，就业面广。',
    '制造产业': '🏭 含机械工程、车辆工程、机器人工程、智能制造工程等专业，是"中国制造2025"核心赛道。新能源汽车带动智能装备需求激增，专精特新企业机械岗位平均年薪超20万。就业方向含汽车主机厂、机器人企业、航空航天院所、新能源产线等。适合动手能力强、空间想象力好的理科生，分数段覆盖广，二本也能找到不错的技术岗。需注意：传统机械岗位工作环境偏工厂、起薪不如IT；建议优先选择机器人工程、智能制造等新兴方向提升竞争力。',
    '基建行业': '🏗️ 含土木工程、建筑学、水利水电、道路桥梁等专业。房建领域需求趋缓，但城市更新、水利水电、一带一路海外工程仍有稳定需求。就业方向含中建/中铁等央企施工单位、建筑设计院、水利部门、工程监理公司等，应届生起薪5000-8000元。适合能吃苦耐劳、喜欢户外实践的学生。需注意：施工单位工作环境艰苦、常年奔波于工地；设计院学历门槛高（硕士起步）；建议女生优先考虑设计/造价方向，男生做好长期出差的心理准备。',
    '临床医学': '🏥 含临床医学（五年制）、口腔医学、麻醉学、眼视光医学等，培养周期为"5年本科+3年规培+X年专培"，对口就业率高达97%。三甲医院普遍要求硕士及以上，博士才有机会留任顶尖医院。应届生月薪约6000元，主治医师月薪1-2万，主任医师年薪可超50万，越老越吃香。适合生物化学好、心理素质强、有同理心的学生。需注意：培养周期10年以上，前期待遇低工作强度大；建议分数500+才报考，口腔医学性价比更高。',
    '医疗健康': '💊 含护理学、药学、医学检验、康复治疗学、医学影像技术等专业。属刚需行业，随老龄化加剧人才缺口持续扩大。护理本科进三甲医院起薪6000-8000元，涉外护理年薪可达20-30万；药学可在医院药房、药企研发或医药销售，研发岗博士起薪30-50万；医学技术岗工作稳定、夜班少。适合细心耐心、动手能力强的学生，中等分数即可报考。需注意：护理工作要值夜班较辛苦；药学研发岗学历门槛高，本科多从事销售或生产岗。',
    '法律专业': '⚖️ 核心专业为法学，必须通过法律职业资格考试（法考，通过率约30%）才能执业。三大就业方向：律师、公务员（公检法）、企业法务。"五院四系"毕业生进红圈所起薪2-3万/月，普通院校竞争压力大。法学与汉语言文学并称"考公两大王牌专业"，考公岗位多选择面广。企业法务在互联网大厂年薪可达50万以上。适合逻辑思维强、记忆力好、善于表达的文科生。需注意：法学已连续多年"红牌"，供过于求；建议500分以上才报考法学，低分院校就业率堪忧。',
    '经管金融': '💰 含金融学、经济学、国际经济与贸易、投资学等专业，是收入天花板最高的大类之一，但两极分化严重——名校+实习+家庭资源是进入投行/券商/基金等高端岗位的关键。银行应届生年薪10-15万，投行/PE年薪30-80万，但普通院校毕业生多从事银行柜员、保险销售等岗位。适合数学好、性格外向、家庭有相关资源的学生。需注意：行业极度看重学历背景，双非院校毕业生上升通道较窄；建议优先考虑经济统计学等有量化技能的方向。',
    '财务专业': '📊 含会计学、审计学、财务管理等专业，是最经典的"万金油"商科方向，任何企业都需要财务人员，就业率稳定在较高水平。职业路径清晰：初级会计→中级会计师→注册会计师(CPA)→财务总监，证书是核心竞争力，CPA持证者年薪可达50万+。四大会计师事务所是黄金起点，起薪1万+/月。适合细心沉稳、对数字敏感的学生，文理兼收。需注意：基础会计岗位面临AI替代风险，必须持续考证提升；四大工作强度极大加班严重，注意平衡生活。',
    '人文社科': '📚 含汉语言文学、哲学、历史学、社会学等专业，最大优势是考公考编岗位多——汉语言文学与法学并称"考公两大王牌"，政府文秘、宣传岗招录量名列前茅。另可从事教师、编辑、新媒体运营、文案策划等。缺点是企业对口岗位少，应届生起薪偏低约4000-6000元。适合语文成绩优异、热爱阅读写作、性格沉稳的文科生。需注意：该专业缺乏硬技能壁垒；建议大学期间主动学习自媒体运营、数据分析等实用技能，提升就业竞争力。',
    '思政教育': '🎯 含思想政治教育、马克思主义理论等专业。随国家对意识形态工作重视和高校"课程思政"推进，该专业近年需求明显回暖。就业方向为中小学政治教师、高校辅导员/思政教师、党政机关公务员、企事业单位党务宣传岗等。应届生起薪约6000元，5年经验可过万。适合政治敏感度高、理论学习能力强、有志从政或教育的学生。考公时有专业对口优势。需注意：专业壁垒不高，所学内容博而不精；若不进体制内，企业就业选择面窄，建议辅修一门实用技能。',
    '教师职业': '📖 含汉语言文学(师范)、数学(师范)、英语(师范)、物理学(师范)等专业，最大优势是稳定有编制、有寒暑假、社会认可度高。部属6所师范院校就业率超95%，公费师范生毕业直接分配无需考编。但近年师范生数量激增，教师编制竞争日趋激烈，双减后教培岗位大幅缩减。适合表达能力强、有耐心、喜欢稳定生活的学生，女生报考比例高。需注意：非公费师范生需自己考编制（某些学科录取比达100:1）；一线城市公立学校教师岗普遍要求硕士学历。',
    '管理学科': '🏢 含工商管理、市场营销、人力资源管理、物流管理等专业。工商管理被称为"商业通用语言"，就业面极宽——可进入各类企业从事管培生、人力资源、市场营销、运营管理等岗位。但"宽"也意味着"浅"，缺乏实习经验则毕业竞争力弱。应届生起薪约6000-8000元/月，3-5年后管理岗年薪可达20万+。适合性格外向、善于沟通、有商业敏感度的学生。需注意：建议名校就读，普通院校该专业竞争力不足；大学期间务必积极实习考取CPA、PMP等证书，选择一个方向深入发展。',
    '传媒专业': '📺 含新闻学、传播学、播音与主持艺术、广播电视编导等专业。传统媒体面临转型压力，但新媒体——短视频创作、直播电商、自媒体运营、品牌营销——需求激增。播音主持可走传统主持或转战自媒体，但头部效应明显：顶尖人才年薪百万，普通从业者收入平平。适合语言表达强、有创意、形象较好的学生。需注意：行业门槛低，非科班同样可进入；内容创作行业竞争激烈熬夜加班多；建议传媒生掌握剪辑、数据分析等复合技能，提升不可替代性。',
    '艺术专业': '🎨 含美术学、音乐学、设计学（视觉传达、环境设计、数字媒体艺术）、舞蹈、戏剧影视等。就业两极分化严重——数字媒体艺术、游戏原画等需求旺盛，大厂校招月薪12-26K，资深岗年薪30万+；纯艺术方向（油画、国画）则依赖天赋和人脉，多数转行或从事美术教育。设计类覆盖全行业，起薪5000-8000元/月。适合有艺术天赋、家庭经济条件较好（艺考培训费用高）的学生。需注意：艺考投入大且就业不确定性高；建议优先选应用型方向（数字媒体/视觉传达）而非纯艺术。',
    '体育专业': '⚽ 含体育教育、运动训练、社会体育指导、运动康复等专业。随"健康中国"战略和全民健身热潮，中小学体育教师缺口约12-24万，运动康复人才缺口约40万。就业方向含中小学体育教师（编制稳定）、健身私教（月薪1.5-3万）、运动康复师、赛事运营（年薪15-30万）等。体育类院校本科就业率约92%，应届生平均月薪约7800元。适合有运动特长、身体素质好的学生，通常需通过体育统考或单招。需注意："学非所用"比例较高，很多毕业生转行销售或行政；教师编制同样竞争激烈，建议同步考取教师资格证和裁判证。',
    '农林食品': '🌾 含农学、园艺、植物保护、动物科学、食品科学与工程等专业。受乡村振兴战略推动，现代农业已从"种地"升级为高科技——智慧农业工程师月薪1.5万，宠物营养师年薪20万，种业研发硕士起薪1.2万。就业方向含农业农村局等政府部门、科研院所、种业/食品企业、农产品电商等。考研竞争压力相对小于热门专业，出国深造机会多。适合对动植物和大自然有浓厚兴趣的学生，分数覆盖面广。需注意：基层岗位工作环境较艰苦、薪资竞争力偏弱；建议选择智慧农业、食品科学等交叉方向。',
    '基础科学': '🔬 含生物科学、化学、环境科学、材料科学与工程等专业，俗称"生化环材"。这四类专业本科就业竞争力较弱——对口岗位多要求硕士甚至博士学历，本科毕业生往往面临"高不成低不就"的尴尬。但并非没有出路：新能源（锂电池/光伏）、生物制药、半导体材料等新兴领域需求旺盛，硕士年薪15-25万、博士30-50万。适合真正热爱科研、愿意读研读博的学生。分数在211线附近用"生化环材"可冲985院校层次。需注意：若本科就业，薪资偏低且工作环境偏实验室/工厂；环境类专业公职岗位有限，考公竞争激烈。',
    '其他专业': '📁 未归入上述分类的专业，含心理学、旅游管理、社会工作、小语种等特色方向。这些专业就业面差异很大——小语种结合商务/技术能力外企前景不错，心理学考研热度高但本科就业面窄，旅游管理受经济周期影响较大。核心选科建议：充分了解该专业对口行业现状、结合个人兴趣和家庭资源、提前规划职业路径（考公/考研/考证）。不建议仅凭专业名称"好听"做选择，一定要查阅该专业近三年的实际就业率数据、平均薪资和主要去向，做出理性判断。',
}



def _detect_major_group(major_name):
    """判断专业所属大类"""
    for group, kws in MAJOR_GROUP_KEYWORDS:
        for kw in kws:
            if kw in major_name:
                return group
    return '其他'


def _detect_major_tags(major_name, std_mid=None):
    """检测专业标签 - 基于数据+知识"""
    tags = []
    
    # 1. 核心特征标签（专业本身属性）
    for pattern, tgs in MAJOR_FEATURE_TAGS.items():
        if any(kw in major_name for kw in pattern.split('|')):
            tags.extend(tgs)
            break
    
    # 2. 热度标签（基于分层数据）
    group = _detect_major_group(major_name)
    if std_mid is not None:
        if std_mid >= 500000:
            tier_key = 'high'
        elif std_mid >= 200000:
            tier_key = 'mid'
        else:
            tier_key = 'low'
        hot = TIER_HOT_LABELS.get(tier_key, {}).get(group)
        if hot:
            tags.append(hot + ('热门' if '🔥' in hot else '冷门'))
    
    return tags if tags else ['📁 其他专业']


def _get_student_guidance(s_std):
    """根据分数段生成引导提示"""
    if s_std >= 500000:
        return {
            'level': 'high',
            'tip': '🎯 高分段！推荐冲击型策略：17个冲刺 + 16个稳妥 + 15个保底',
            'advice': '高分优先选名校，理工科看专业，文科看学校，城市也很重要',
        }
    elif s_std >= 200000:
        return {
            'level': 'mid',
            'tip': '📊 中分段，推荐均衡策略：10个冲刺 + 30个稳妥 + 24个保底',
            'advice': '中等分数优先本省院校，名额多录取概率高',
        }
    else:
        return {
            'level': 'low',
            'tip': '🛡️ 低分段，建议稳妥型策略：4个冲刺 + 24个稳妥 + 20个保底',
            'advice': '400-480分段，能上本科不上专科，公办专科优先',
        }


def _norm_cat(cat):
    return CAT_MAP.get(cat, cat)


# ========== 数据加载 ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_data()
    yield

app = FastAPI(title="河南高考志愿推荐系统", version="3.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _load_data():
    print("加载数据中...")

    # 1. 标准化排位分
    fp = os.path.join(PROCESSED_DIR, 'standardized_scores.json')
    with open(fp, 'r', encoding='utf-8') as f:
        for r in json.load(f)['data']:
            STANDARDIZED[(r['year'], r['category'], r['score'])] = r
    print(f"  标准化排位分: {len(STANDARDIZED)} 条")

    # 2. 专业标准化（历年）- 按专业合并区间
    fp = os.path.join(PROCESSED_DIR, 'major_standards.json')
    with open(fp, 'r', encoding='utf-8') as f:
        major_data = json.load(f)['data']
    # 按 (year, school, major) 索引
    for r in major_data:
        key = (r['year'], r['school'], r['major'])
        if key not in MAJOR_STD:
            MAJOR_STD[key] = r
        else:
            # 合并区间（取更宽范围）
            old = MAJOR_STD[key]
            MAJOR_STD[key] = {
                'year': r['year'],
                'school': r['school'],
                'major': r['major'],
                'low_std': min(old['low_std'], r['low_std']),
                'high_std': max(old['high_std'], r['high_std']),
                'low_rank': min(old['low_rank'], r['low_rank']),
                'high_rank': max(old['high_rank'], r['high_rank']),
            }
    print(f"  专业标准化: {len(MAJOR_STD)} 条")

    # 3. 学校标准化
    fp = os.path.join(PROCESSED_DIR, 'school_standards.json')
    with open(fp, 'r', encoding='utf-8') as f:
        for r in json.load(f)['data']:
            SCHOOL_STD[(r['year'], r['school'], r.get('category', 'physics'))] = r
    print(f"  学校标准化: {len(SCHOOL_STD)} 条")

    # 4. 专业组标准化
    fp = os.path.join(PROCESSED_DIR, 'group_standards.json')
    with open(fp, 'r', encoding='utf-8') as f:
        for r in json.load(f)['data']:
            GROUP_STD[(r['school'], r['group_code'], r['category'])] = r
    print(f"  专业组标准化: {len(GROUP_STD)} 条")

    # 5. 专业组专业列表
    fp = os.path.join(PROCESSED_DIR, 'group_majors.json')
    with open(fp, 'r', encoding='utf-8') as f:
        for g in json.load(f)['data']:
            GROUP_MAJORS[(g['school'], g['group_code'], g['category'])] = g['majors']
    print(f"  专业组结构: {len(GROUP_MAJORS)} 组")

    # 6. 总人数
    fp = os.path.join(PROCESSED_DIR, 'total_counts.json')
    with open(fp, 'r', encoding='utf-8') as f:
        for ys, cats in json.load(f).items():
            for c, cnt in cats.items():
                TOTAL_COUNTS[(int(ys), c)] = cnt

    # 7. 构建学校→省份映射 & 专业→类别映射
    all_schools = set()
    for (_, school, major) in MAJOR_STD:
        all_schools.add(school)
        if (school, major) not in MAJOR_CATEGORY:
            MAJOR_CATEGORY[(school, major)] = _detect_major_category(major)
    for (school, _, _) in GROUP_STD:
        all_schools.add(school)

    for s in all_schools:
        SCHOOL_PROVINCE[s] = _detect_province(s)

    prov_count = defaultdict(int)
    for s, p in SCHOOL_PROVINCE.items():
        prov_count[p] += 1
    print(f"  省份覆盖: {len(prov_count)} 个")
    for p, c in sorted(prov_count.items(), key=lambda x: -x[1]):
        print(f"    {p}: {c} 所学校")

    print("数据加载完成 ✅")


# ========== 匹配算法 ==========

def _score_match(s_low, s_high, t_low, t_high):
    """计算匹配度，返回 (tier, rel_pos, confidence)"""
    s_mid = (s_low + s_high) / 2
    t_center = (t_low + t_high) / 2
    t_radius = max((t_high - t_low) / 2, 1)
    rel_pos = (s_mid - t_center) / t_radius

    overlap = max(0, min(s_high, t_high) - max(s_low, t_low))
    if rel_pos < -1:
        dist = rel_pos + 1
        conf = max(0, min(1, 1 + dist * 0.3))
        if rel_pos < -3:
            return 'impossible', rel_pos, 0
        return 'chong', rel_pos, max(0.05, conf)
    elif rel_pos > 1:
        dist = rel_pos - 1
        conf = max(0, min(1, 1 - dist * 0.3))
        if rel_pos > 3:
            return 'waste', rel_pos, 1
        return 'bao', rel_pos, min(1, conf + 0.3)
    else:
        centered = 1 - abs(rel_pos)
        conf = 0.5 + centered * 0.4
        return 'wen', rel_pos, min(0.95, conf)


def _format_prob(tier, rel_pos):
    """将匹配度映射为展示概率"""
    if tier == 'chong':
        closeness = max(0, 1 - abs(rel_pos + 1) / 3)
        prob = round(closeness * 25 + 3)
        return max(1, min(30, prob))
    elif tier == 'wen':
        centered = 1 - abs(rel_pos)
        prob = round(centered * 30 + 38)
        return max(30, min(70, prob))
    elif tier == 'bao':
        closeness = max(0, 1 - (rel_pos - 1) / 3)
        prob = round(closeness * 25 + 72)
        return max(70, min(98, prob))
    else:
        return 0


# ========== 页面 ==========

@app.get("/")
async def index():
    return FileResponse(os.path.join(FRONTEND_DIR, 'index.html'))


# ========== 元数据 API ==========

@app.get("/api/years")
async def list_years():
    years = sorted(set(k[0] for k in STANDARDIZED.keys()), reverse=True)
    return {'years': years}


@app.get("/api/provinces")
async def list_provinces():
    provs = sorted(set(SCHOOL_PROVINCE.values()))
    return {'provinces': provs}


@app.get("/api/categories")
async def list_categories():
    return {'categories': ALL_CATEGORIES}


@app.get("/api/subject-requirements")
async def list_subject_requirements():
    return {'requirements': ['不限', '政', '地', '化', '生', '化且地', '化且生', '政且地', '生且政', '化且政']}


# ========== 查询 API ==========

@app.get("/api/query")
async def query_score(score: int = Query(...), year: int = Query(...), category: str = Query(...)):
    cat = _norm_cat(category)
    key = (year, cat, score)
    if key not in STANDARDIZED:
        raise HTTPException(status_code=404, detail=f"未找到 {year}年{category}{score}分的数据")
    r = STANDARDIZED[key]
    isotonic = {}
    mid_rank = (r['high_rank'] + r['low_rank']) // 2
    for (oy, oc, _), or2 in STANDARDIZED.items():
        if oc == cat and oy != year:
            if or2['high_rank'] <= mid_rank <= or2['low_rank']:
                isotonic[oy] = or2['score']
    for (oy, oc, _), or2 in STANDARDIZED.items():
        if oc == cat and oy != year and oy not in isotonic:
            diff = abs(or2['low_rank'] - mid_rank)
            if diff < 10000:
                isotonic.setdefault(oy, or2['score'])
    return {
        'query': {'score': score, 'year': year, 'category': category},
        'standardized_range': {
            'low': r['low_std'], 'high': r['high_std'],
            'rank_low': r['low_rank'], 'rank_high': r['high_rank'],
        },
        'same_score_count': r['count'],
        'total_students': TOTAL_COUNTS.get((year, cat), 0),
        'isotonic_scores': isotonic,
        'summary': f"{year}年{category}{score}分，同分{r['count']:,}人，位次{r['high_rank']:,}~{r['low_rank']:,}名",
    }


# ========== 推荐 API（核心）==========

@app.get("/api/recommend")
async def recommend(
    score: int = Query(...),
    year: int = Query(...),
    category: str = Query(...),
    province: str = Query(None, description="省份筛选"),
    major_category: str = Query(None, description="专业类别筛选"),
    subject_req: str = Query(None, description="选科要求（仅2025年生效）"),
    strategy: str = Query('auto', description="冲稳保策略：auto/aggressive/balanced/safe"),
    tag_filter: str = Query(None, description="专业标签筛选"),
):
    cat = _norm_cat(category)
    sk = (year, cat, score)
    if sk not in STANDARDIZED:
        raise HTTPException(status_code=404, detail="未找到该分数数据")

    sr = STANDARDIZED[sk]
    s_low, s_high = sr['low_std'], sr['high_std']

    # 动态冲稳保配置
    s_mid = (s_low + s_high) / 2
    # 策略映射：auto=自动, aggressive=冲击型, balanced=均衡型, safe=稳妥型
    STRATEGIES = {
        'aggressive': (17, 16, 15),
        'balanced': (10, 30, 24),
        'safe': (4, 24, 20),
    }
    if strategy in STRATEGIES:
        CHONG_N, WEN_N, BAO_N = STRATEGIES[strategy]
    else:
        # auto：根据标准化分自动选择
        if s_mid >= 500000:
            CHONG_N, WEN_N, BAO_N = 17, 16, 15
        elif s_mid >= 200000:
            CHONG_N, WEN_N, BAO_N = 10, 30, 24
        else:
            CHONG_N, WEN_N, BAO_N = 4, 24, 20
    candidates = []

    if year >= 2025:
        # === 2025新高考 → 专业组推荐 ===
        tcat = CAT_REVERSE.get(cat, cat)
        for (sch, gcode, gcat), gr in GROUP_STD.items():
            if gcat != tcat or gr['high_std'] is None:
                continue

            # 省份筛选
            if province and province != '全部':
                sp = SCHOOL_PROVINCE.get(sch, '其他')
                if sp != province:
                    continue

            # 专业类别筛选：专业组内任意专业匹配即通过
            if major_category and major_category != '全部':
                majors = GROUP_MAJORS.get((sch, gcode, tcat), [])
                has_match = any(
                    MAJOR_CATEGORY.get((sch, m['name']), '其他') == major_category
                    for m in majors
                )
                if not has_match:
                    continue

            # 选科要求筛选
            if subject_req and subject_req != '全部':
                grp_req = str(gr.get('subject_req', '')).strip()
                if subject_req == '不限':
                    pass  # 不限选科的专业组都可通过
                elif grp_req and grp_req != '不限' and subject_req not in grp_req:
                    continue

            tier, rel_pos, _ = _score_match(s_low, s_high, gr['low_std'], gr['high_std'])
            if tier in ('waste', 'impossible'):
                continue

            majors = GROUP_MAJORS.get((sch, gcode, tcat), [])
            major_names = [m['name'] for m in majors[:6]]
            majors_category = set(MAJOR_CATEGORY.get((sch, m['name']), '其他') for m in majors)

            prob = _format_prob(tier, rel_pos)
            candidates.append({
                'school': sch,
                'province': SCHOOL_PROVINCE.get(sch, '其他'),
                'group_code': gcode,
                'majors': major_names,
                'majors_category': list(majors_category),
                'major_count': len(majors),
                'subject_req': gr.get('subject_req', ''),
                'tier': tier,
                'probability': prob,
                'rel_pos': rel_pos,
            })
    else:
        # === 旧高考 → 专业推荐 ===
        for (m_year, school, major), mr in MAJOR_STD.items():
            if m_year != year:
                continue

            # 省份筛选
            if province and province != '全部':
                sp = SCHOOL_PROVINCE.get(school, '其他')
                if sp != province:
                    continue

            # 专业类别筛选
            if major_category and major_category != '全部':
                mc = MAJOR_CATEGORY.get((school, major), '其他')
                if mc != major_category:
                    continue

            tier, rel_pos, _ = _score_match(s_low, s_high, mr['low_std'], mr['high_std'])
            if tier in ('waste', 'impossible'):
                continue

            prob = _format_prob(tier, rel_pos)
            candidates.append({
                'school': school,
                'province': SCHOOL_PROVINCE.get(school, '其他'),
                'major': major,
                'major_category': MAJOR_CATEGORY.get((school, major), '其他'),
                'tier': tier,
                'probability': prob,
                'rel_pos': rel_pos,
            })

    # === 分档取数 ===
    chong = [c for c in candidates if c['tier'] == 'chong']
    wen = [c for c in candidates if c['tier'] == 'wen']
    bao = [c for c in candidates if c['tier'] == 'bao']

    chong.sort(key=lambda x: abs(x['rel_pos'] + 1))
    wen.sort(key=lambda x: abs(x['rel_pos']))
    bao.sort(key=lambda x: abs(x['rel_pos'] - 1))

    picks = chong[:CHONG_N] + wen[:WEN_N] + bao[:BAO_N]

    # 去重：同一学校+专业（往年）或同一专业组（2025）只保留一次
    seen = set()
    deduped = []
    for p in picks:
        if year >= 2025:
            key = (p['school'], p['group_code'])
        else:
            key = (p['school'], p['major'])
        if key not in seen:
            seen.add(key)
            deduped.append(p)

    tier_order = {'chong': 0, 'wen': 1, 'bao': 2}
    deduped.sort(key=lambda x: (tier_order.get(x['tier'], 99), -x['probability']))

    # 添加专业标签
    for rec in deduped:
        if year >= 2025:
            for m_name in rec.get('majors', []):
                if not rec.get('tags'):
                    rec['tags'] = _detect_major_tags(m_name, s_mid)
                if rec.get('tags'):
                    break
            if not rec.get('tags'):
                rec['tags'] = ['📁 其他专业']
        else:
            rec['tags'] = _detect_major_tags(rec.get('major', ''), s_mid)

    # 标签筛选
    if tag_filter and tag_filter != '全部':
        deduped = [rec for rec in deduped if any(tag_filter in tag for tag in rec.get('tags', []))]

    # 策略名称
    strategy_names = {'aggressive': '冲击型', 'balanced': '均衡型', 'safe': '稳妥型', 'auto': '自动'}
    strategy_name = strategy_names.get(strategy, '自动')
    if strategy == 'auto':
        if CHONG_N == 17:
            strategy_name = '自动(冲击型)'
        elif CHONG_N == 4:
            strategy_name = '自动(稳妥型)'
        else:
            strategy_name = '自动(均衡型)'

    # 生成引导提示
    guidance = _get_student_guidance(s_mid)

    for rec in deduped:
        rec["advice"] = guidance.get("advice", "名师建议：根据分数段合理选择")
    return {
        'query': {'score': score, 'year': year, 'category': category, 'province': province,
                   'major_category': major_category, 'subject_req': subject_req},
        'student_range': {'low': s_low, 'high': s_high},
        'student_std': s_mid,
        'tier_config': {'chong_n': CHONG_N, 'wen_n': WEN_N, 'bao_n': BAO_N, 'strategy_name': strategy_name},
        'total_candidates': len(candidates),
        'tier_counts': {
            'chong': min(len(chong), CHONG_N),
            'wen': min(len(wen), WEN_N),
            'bao': min(len(bao), BAO_N),
        },
        'guidance': guidance,
        'recommendations': deduped,
    }


# ========== 详情 API ==========

@app.get("/api/school/{school_name}")
async def school_info(school_name: str, year: int = Query(None)):
    results = []
    for (sy, sn, sc), r in SCHOOL_STD.items():
        if sn == school_name and (year is None or sy == year):
            results.append({
                'year': sy, 'school': sn, 'category': sc, 'province': SCHOOL_PROVINCE.get(sn, '其他'),
                'range': {'low': r['low_std'], 'high': r['high_std']},
            })
    if not results:
        raise HTTPException(status_code=404, detail=f"未找到学校: {school_name}")
    results.sort(key=lambda x: -x['year'])
    return {'school': school_name, 'province': SCHOOL_PROVINCE.get(school_name, '其他'), 'data': results}


@app.get("/api/group/{school_name}/{group_code}")
async def group_info(school_name: str, group_code: str, category: str = Query('物理')):
    tcat = CAT_REVERSE.get(_norm_cat(category), category)
    gkey = (school_name, group_code, tcat)
    std = GROUP_STD.get(gkey)
    majors = GROUP_MAJORS.get(gkey, [])
    if not majors and std is None:
        raise HTTPException(status_code=404)
    return {
        'school': school_name, 'group_code': group_code,
        'category': category, 'province': SCHOOL_PROVINCE.get(school_name, '其他'),
        'standardized_range': {'low': std['low_std'], 'high': std['high_std']} if std else None,
        'majors': majors,
    }


# ========== 数据下载 API ==========

DATA_FILES = {
    'standardized_scores.json': '标准化排位分（历年一分一段表映射到 0~1M）',
    'major_standards.json': '专业标准化数据（每年每个学校每个专业的排位分区间）',
    'school_standards.json': '学校标准化数据（每年每个学校的排位分区间）',
    'group_standards.json': '专业组标准化数据（2025 新高考专业组排位分区间）',
    'group_majors.json': '专业组专业列表（2025 各组包含的具体专业）',
    'total_counts.json': '各年各科类总考生人数',
}


@app.get("/api/data-files")
async def list_data_files():
    """返回可下载的数据文件列表"""
    files = []
    for name, desc in DATA_FILES.items():
        fp = os.path.join(PROCESSED_DIR, name)
        size = os.path.getsize(fp) if os.path.exists(fp) else 0
        files.append({
            'filename': name,
            'description': desc,
            'size': size,
            'size_mb': round(size / 1024 / 1024, 2),
        })
    return {'files': files}


@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """下载指定的数据文件"""
    # 安全校验：只允许 DATA_FILES 中列出的文件名
    if filename not in DATA_FILES:
        raise HTTPException(status_code=404, detail='文件不存在')
    fp = os.path.join(PROCESSED_DIR, filename)
    if not os.path.exists(fp):
        raise HTTPException(status_code=404, detail='文件未找到')
    return FileResponse(fp, filename=filename, media_type='application/json')


# ========== 艺术体育类 API ==========

from art_sport import ART_CATEGORIES, get_recommendations


@app.get("/api/tag-filters")
async def list_tag_filters():
    """返回标签筛选选项"""
    filters = ['全部'] + sorted(set(
        t.split(' ')[1] if ' ' in t else t
        for tags in MAJOR_FEATURE_TAGS.values()
        for t in tags
    ))
    return {'filters': filters}


@app.get("/api/strategies")
async def list_strategies():
    """返回策略选项"""
    return {
        'strategies': [
            {'id': 'auto', 'name': '🔄 自动推荐'},
            {'id': 'aggressive', 'name': '🚀 冲击型 (17冲/16稳/15保)'},
            {'id': 'balanced', 'name': '⚖️ 均衡型 (10冲/30稳/24保)'},
            {'id': 'safe', 'name': '🛡️ 稳妥型 (4冲/24稳/20保)'},
        ]
    }


@app.get("/api/art-categories")
@app.get("/api/tag-descriptions")
async def list_tag_descriptions():
    """返回专业标签详细说明字典"""
    return {'descriptions': TAG_DESCRIPTIONS}

async def list_art_categories():
    """返回艺术体育类别列表"""
    return {'categories': ART_CATEGORIES}


@app.get("/api/art-recommend")
async def art_recommend(
    culture: int = Query(..., description='文化课分数'),
    major: int = Query(..., description='专业课分数'),
    category: str = Query(..., description='艺术类别'),
):
    """艺术体育类志愿推荐（按概率排序，无冲稳保）"""
    recs = get_recommendations(culture, major, category)
    return {
        'query': {'culture': culture, 'major': major, 'category': category},
        'total': len(recs),
        'recommendations': recs,
    }


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
