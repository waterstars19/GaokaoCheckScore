"""
河南高考数据查询API
用法: from query import load; q = load(); q.score_to_rank(610, 2024, '理科')
"""
import json, os, glob
from bisect import bisect_left, bisect_right
from collections import defaultdict

DATA_DIR = os.path.dirname(os.path.abspath(__file__))


# Category normalization: 一分一段表 uses history/physics, 录取数据 uses 文科/理科
CAT_MAP = {
    '理科': 'physics', '物理类': 'physics', 'physics': 'physics',
    '文科': 'history', '历史类': 'history', 'history': 'history',
}
CAT_REVERSE = {'physics': '理科', 'history': '文科'}

def _norm_cat(cat):
    return CAT_MAP.get(cat, cat)

class QueryAPI:
    def __init__(self):
        self.yiduan = {}       # (year, cat) -> [(score, count, cum), ...] cat normalized to physics/history
        self.admission = {}     # (year, cat) -> [(min_score, min_rank, school, major), ...] cat = 理科/文科
        self.all_records = []   # all admission records
        self._loaded = False

    def load(self):
        """加载所有数据"""
        if self._loaded:
            return self

        # 1. 一分一段表 (normalize category to physics/history)
        fp = os.path.join(DATA_DIR, '河南一分一段表_2017-2025.json')
        with open(fp, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for r in data['data']:
            cat = _norm_cat(r['category'])
            key = (r['year'], cat)
            if key not in self.yiduan:
                self.yiduan[key] = []
            self.yiduan[key].append((r['score'], r['count'], r['cumulative']))

        # Sort each by score descending
        for key in self.yiduan:
            self.yiduan[key].sort(key=lambda x: -x[0])

        # 2. 录取数据 (keep as 理科/文科 for display, but store internally with normalized cat)
        for fp in glob.glob(os.path.join(DATA_DIR, '河南_*分_历年录取数据.json')):
            with open(fp, 'r', encoding='utf-8') as f:
                adata = json.load(f)
            for r in adata['data']:
                self.all_records.append(r)
                cat = _norm_cat(r['category'])
                key = (r['year'], cat)
                if key not in self.admission:
                    self.admission[key] = []
                self.admission[key].append((
                    r['min_score'], r['min_rank'] or 0,
                    r['school'], r.get('major', ''),
                    r.get('max_score'), r.get('source', '')
                ))

        # Sort admission by rank ascending (best rank first)
        for key in self.admission:
            self.admission[key].sort(key=lambda x: x[1] if x[1] > 0 else 9999999)

        self._loaded = True
        print(f'Loaded: {len(self.yiduan)} score tables, {len(self.admission)} admission tables, {len(self.all_records)} total records')
        return self

    # ========== 位次查询 ==========

    def score_to_rank(self, score, year, category):
        """分数 → 位次（一次遍历，同时处理精确匹配和向下取整）"""
        cat = _norm_cat(category)
        key = (year, cat)
        if key not in self.yiduan:
            return None
        data = self.yiduan[key]  # sorted by score desc
        # 一次遍历：先找精确匹配，再找第一个低于目标的分数（向下取整）
        for s, cnt, cum in data:
            if s <= score:
                return cum
        return None

    def rank_to_score(self, rank, year, category):
        """位次 → 分数"""
        cat = _norm_cat(category)
        key = (year, cat)
        if key not in self.yiduan:
            return None
        data = self.yiduan[key]
        for s, cnt, cum in data:
            if cum >= rank:
                return s
        return data[-1][0] if data else None

    # ========== 同位分换算 ==========

    def isotonic_score(self, score, from_year, category, to_year):
        """将 from_year 的分数换算为 to_year 的等效分"""
        rank = self.score_to_rank(score, from_year, category)
        if rank is None:
            return None
        return self.rank_to_score(rank, to_year, category)

    # ========== 院校查询 ==========

    def query_schools(self, score=None, rank=None, year=None, category=None,
                      score_range=None, limit=50):
        """查询院校：按分数或位次，返回匹配的专业记录"""
        cat = _norm_cat(category)
        if rank is None and score is not None and year is not None and category is not None:
            rank = self.score_to_rank(score, year, category)
        if rank is None:
            return [], None

        key = (year, cat)
        if key not in self.admission:
            return [], rank

        records = self.admission[key]

        if score_range is None:
            score_range = 3000  # default: ±3000 rank

        lo = max(0, rank - score_range)
        hi = rank + score_range

        results = []
        seen = set()
        for min_score, min_rank, school, major, max_score, source in records:
            if lo <= min_rank <= hi:
                key2 = (year, school, major, min_score)
                if key2 not in seen:
                    seen.add(key2)
                    results.append({
                        'school': school, 'major': major,
                        'min_score': min_score, 'min_rank': min_rank,
                        'max_score': max_score, 'source': source,
                    })

        # Sort and categorize: 冲 (>rank), 稳 (near), 保 (<rank)
        for r in results:
            if r['min_rank'] < rank - 1000:
                r['tier'] = '冲'
            elif r['min_rank'] > rank + 1000:
                r['tier'] = '保'
            else:
                r['tier'] = '稳'

        results.sort(key=lambda x: x['min_rank'])
        return results[:limit], rank

    # ========== 便捷方法 ==========

    def search(self, score, year, category='理科', margin=3000, limit=30):
        """一站式查询：分数 → 位次 + 同位分 + 院校推荐"""
        rank = self.score_to_rank(score, year, category)
        if rank is None:
            return {'error': f'No data for {year} {category} score {score}'}

        # 同位分换算到所有年份
        iso = {}
        for y in [2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017]:
            if y == year:
                continue
            s = self.rank_to_score(rank, y, category)
            if s is not None:
                iso[y] = s

        # 查院校
        schools, _ = self.query_schools(rank=rank, year=year, category=category,
                                         score_range=margin, limit=limit)

        return {
            'query': {'score': score, 'year': year, 'category': category},
            'rank': rank,
            'isotonic': iso,
            'schools': schools,
        }

    def compare(self, score, category='理科', margin=3000, years=None):
        """跨年对比：同一分数在历年的位次和院校"""
        if years is None:
            years = [2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017]
        results = []
        for y in years:
            r = self.search(score, y, category, margin=margin, limit=10)
            results.append(r)
        return results

    def top_schools(self, year=2024, category='理科', limit=20):
        """查看某年最高分的院校"""
        key = (year, category)
        if key not in self.admission:
            return []
        records = self.admission[key]
        seen = set()
        result = []
        for min_score, min_rank, school, major, max_score, source in records:
            if school not in seen:
                seen.add(school)
                result.append({'school': school, 'min_score': min_score, 'min_rank': min_rank})
            if len(result) >= limit:
                break
        return result


# ========== 全局单例 ==========
_inst = None

def load():
    global _inst
    if _inst is None:
        _inst = QueryAPI().load()
    return _inst
