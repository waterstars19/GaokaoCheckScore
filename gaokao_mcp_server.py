#!/usr/bin/env python
"""
高考数据查询 MCP Server
提供分数查询、位次换算、院校推荐等工具
"""
import json, sys, os

# Add parent dir to path for query module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from query import load

# Lazy init
_qa = None

def get_qa():
    global _qa
    if _qa is None:
        _qa = load()
    return _qa


TOOLS = [
    {
        "name": "gaokao_score_to_rank",
        "description": "查询河南高考某个分数在指定年份和科类中的全省位次（累计人数）。例如：输入610分、2024年、理科，返回该分数对应的全省排名。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "score": {"type": "integer", "description": "高考分数，如 610"},
                "year": {"type": "integer", "description": "年份，如 2024"},
                "category": {"type": "string", "description": "科类：'理科'/'物理类' 或 '文科'/'历史类'"},
            },
            "required": ["score", "year", "category"],
        },
    },
    {
        "name": "gaokao_rank_to_score",
        "description": "根据全省位次反查对应的分数。例如：位次10000名在2024年理科对应多少分。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "rank": {"type": "integer", "description": "全省位次（累计人数），如 10000"},
                "year": {"type": "integer", "description": "年份"},
                "category": {"type": "string", "description": "科类"},
            },
            "required": ["rank", "year", "category"],
        },
    },
    {
        "name": "gaokao_isotonic_score",
        "description": "同位分换算：将某年的分数换算为另一年的等效分数。用于跨年志愿参考。例如：2024年理科610分相当于2023年的多少分。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "score": {"type": "integer", "description": "原始分数"},
                "from_year": {"type": "integer", "description": "原始年份"},
                "category": {"type": "string", "description": "科类"},
                "to_year": {"type": "integer", "description": "目标年份"},
            },
            "required": ["score", "from_year", "category", "to_year"],
        },
    },
    {
        "name": "gaokao_search_schools",
        "description": "一站式查询：输入分数+年份+科类，返回位次、历年同位分、以及冲稳保院校推荐。这是最常用的查询接口。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "score": {"type": "integer", "description": "高考分数"},
                "year": {"type": "integer", "description": "年份，可选2025/2024/2023/2022/2021/2020/2019/2018/2017"},
                "category": {"type": "string", "description": "科类：'理科' 或 '文科'"},
                "margin": {"type": "integer", "description": "位次浮动范围，默认3000（即查找位次±3000以内的院校）", "default": 3000},
                "limit": {"type": "integer", "description": "返回院校数量上限，默认30", "default": 30},
            },
            "required": ["score", "year", "category"],
        },
    },
    {
        "name": "gaokao_compare_years",
        "description": "跨年对比：同一分数在多个年份的位次和院校变化。用于理解分数含金量的年际波动。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "score": {"type": "integer", "description": "高考分数"},
                "category": {"type": "string", "description": "科类"},
                "years": {"type": "string", "description": "要对比的年份，逗号分隔，如 '2024,2023,2022'。默认最近5年"},
            },
            "required": ["score", "category"],
        },
    },
    {
        "name": "gaokao_batch_score_query",
        "description": "批量查询：一次查询多个分数在同一年的位次。适合快速对比多个考生的排名。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scores": {"type": "string", "description": "分数列表，逗号分隔，如 '680,650,600,550,500'"},
                "year": {"type": "integer", "description": "年份"},
                "category": {"type": "string", "description": "科类"},
            },
            "required": ["scores", "year", "category"],
        },
    },
]


def handle_tools_list():
    return {"tools": TOOLS}


def handle_tools_call(name, arguments):
    qa = get_qa()

    try:
        if name == "gaokao_score_to_rank":
            rank = qa.score_to_rank(arguments["score"], arguments["year"], arguments["category"])
            if rank is None:
                return {"_error": f"未找到{arguments['year']}年{arguments['category']}{arguments['score']}分的数据"}
            return {
                "score": arguments["score"],
                "year": arguments["year"],
                "category": arguments["category"],
                "rank": rank,
                "summary": f"{arguments['year']}年{arguments['category']}{arguments['score']}分，全省位次约第{rank:,}名"
            }

        elif name == "gaokao_rank_to_score":
            score = qa.rank_to_score(arguments["rank"], arguments["year"], arguments["category"])
            if score is None:
                return {"_error": f"未找到{arguments['year']}年{arguments['category']}位次{arguments['rank']}的数据"}
            return {
                "rank": arguments["rank"],
                "year": arguments["year"],
                "category": arguments["category"],
                "score": score,
                "summary": f"{arguments['year']}年{arguments['category']}位次{arguments['rank']:,}对应约{score}分"
            }

        elif name == "gaokao_isotonic_score":
            rank = qa.score_to_rank(arguments["score"], arguments["from_year"], arguments["category"])
            if rank is None:
                return {"_error": f"未找到{arguments['from_year']}年{arguments['category']}{arguments['score']}分的位次数据，无法换算"}
            iso = qa.rank_to_score(rank, arguments["to_year"], arguments["category"])
            if iso is None:
                return {"_error": f"位次{rank}在{arguments['to_year']}年{arguments['category']}中无对应分数"}
            return {
                "original": {"score": arguments["score"], "year": arguments["from_year"], "rank": rank},
                "converted": {"score": iso, "year": arguments["to_year"]},
                "summary": f"{arguments['from_year']}年{arguments['category']}{arguments['score']}分(位次{rank:,}) 等效于 {arguments['to_year']}年{iso}分"
            }

        elif name == "gaokao_search_schools":
            result = qa.search(
                arguments["score"], arguments["year"], arguments["category"],
                margin=arguments.get("margin", 3000),
                limit=arguments.get("limit", 30)
            )
            if "error" in result:
                return {"_error": result["error"]}

            tiers = {"冲": [], "稳": [], "保": []}
            for s in result["schools"]:
                major_short = s['major'][:40] if s['major'] else '(院校投档线)'
                tiers[s['tier']].append({
                    "school": s['school'],
                    "score": s['min_score'],
                    "rank": s['min_rank'],
                    "major": major_short,
                })

            iso_summary = ", ".join(f"{y}年≈{s}分" for y, s in sorted(result['isotonic'].items(), reverse=True))

            return {
                "query": result["query"],
                "rank": result["rank"],
                "isotonic_scores": result["isotonic"],
                "isotonic_summary": iso_summary,
                "recommendations": tiers,
                "summary": (
                    f"{result['query']['year']}年{result['query']['category']}{result['query']['score']}分，"
                    f"全省位次第{result['rank']:,}名。"
                    f"同位分：{iso_summary}。"
                    f"冲{len(tiers['冲'])}所、稳{len(tiers['稳'])}所、保{len(tiers['保'])}所院校。"
                )
            }

        elif name == "gaokao_compare_years":
            years_str = arguments.get("years", "2024,2023,2022,2021,2020")
            years = [int(y.strip()) for y in years_str.split(",")]
            results = qa.compare(arguments["score"], arguments["category"], years=years)

            comparison = []
            for r in results:
                if "error" in r:
                    comparison.append({"year": r.get("query", {}).get("year", "?"), "error": r["error"]})
                else:
                    top_schools = [s['school'] for s in r.get('schools', [])[:3]]
                    comparison.append({
                        "year": r['query']['year'],
                        "score": r['query']['score'],
                        "rank": r['rank'],
                        "isotonic_to": r.get('isotonic', {}),
                        "sample_schools": top_schools,
                    })

            return {
                "score": arguments["score"],
                "category": arguments["category"],
                "comparison": comparison,
                "summary": f"{arguments['category']}{arguments['score']}分在不同年份的全省位次对比"
            }

        elif name == "gaokao_batch_score_query":
            scores = [int(s.strip()) for s in arguments["scores"].split(",")]
            results = []
            for s in scores:
                rank = qa.score_to_rank(s, arguments["year"], arguments["category"])
                results.append({
                    "score": s,
                    "rank": rank,
                    "summary": f"{s}分 → 位次{rank:,}" if rank else f"{s}分 → 无数据"
                })
            return {
                "year": arguments["year"],
                "category": arguments["category"],
                "results": results,
                "summary": f"{arguments['year']}年{arguments['category']}批量查询完成"
            }

        return {"_error": f"未知工具: {name}"}

    except KeyError as e:
        return {"_error": f"缺少必要参数: {e}"}
    except Exception as e:
        return {"_error": f"查询异常: {e}"}


def _build_text_content(data):
    """将工具返回数据包装为 MCP 标准 content 数组"""
    text = json.dumps(data, ensure_ascii=False)
    return {"content": [{"type": "text", "text": text}]}


def _build_error_content(err_msg):
    """将错误信息包装为 MCP 标准 error content"""
    text = json.dumps({"error": err_msg}, ensure_ascii=False)
    return {
        "content": [{"type": "text", "text": text}],
        "isError": True,
    }


def main():
    # Init on startup
    get_qa()

    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
        except json.JSONDecodeError:
            continue

        method = request.get("method")
        req_id = request.get("id")

        try:
            if method == "tools/list":
                response = handle_tools_list()
            elif method == "tools/call":
                params = request.get("params", {})
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                result = handle_tools_call(tool_name, arguments)
                if "_error" in result:
                    response = _build_error_content(result["_error"])
                else:
                    response = _build_text_content(result)
            elif method == "initialize":
                response = {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "gaokao-query", "version": "1.0.0"},
                    "capabilities": {"tools": {}},
                }
            else:
                # JSON-RPC 标准 error 格式
                output = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"未知方法: {method}",
                    },
                }
                sys.stdout.write(json.dumps(output, ensure_ascii=False) + "\n")
                sys.stdout.flush()
                continue
        except Exception as e:
            response = _build_error_content(f"服务器内部错误: {e}")

        output = {"jsonrpc": "2.0", "id": req_id, "result": response}
        sys.stdout.write(json.dumps(output, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
