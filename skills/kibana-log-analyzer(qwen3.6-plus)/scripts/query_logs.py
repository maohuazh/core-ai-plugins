#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kibana日志查询脚本
支持: 错误日志分组统计、调用链追踪、trace详情查询
"""

import json
import sys
import subprocess
from datetime import datetime, timedelta


def run_curl(url, method="GET", data=None):
    """执行curl命令并返回JSON结果"""
    cmd = ["curl", "-s", "-X", method, url, "-H", "Content-Type: application/json"]
    if data:
        cmd.extend(["-d", json.dumps(data)])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"Error: {result.stderr}", file=sys.stderr)
            return None
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Exception: {e}", file=sys.stderr)
        return None


def query_error_groups(kibana_url, date_str, app_filter=None, hours=1):
    """
    查询错误日志分组统计
    按 app -> action -> error_code 分组
    """
    index = f"action-{date_str}"
    
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"result": "ERROR"}},
                    {"range": {"@timestamp": {"gte": f"now-{hours}h"}}}
                ]
            }
        },
        "size": 0,
        "aggs": {
            "by_app": {
                "terms": {"field": "app", "size": 50},
                "aggs": {
                    "by_action": {
                        "terms": {"field": "action", "size": 50},
                        "aggs": {
                            "by_error": {
                                "terms": {"field": "error_code", "size": 50},
                                "aggs": {
                                    "sample_hit": {
                                        "top_hits": {
                                            "size": 1,
                                            "sort": [{"@timestamp": "desc"}],
                                            "_source": [
                                                "id", "@timestamp", "app", "action",
                                                "error_code", "error_message",
                                                "ref_id", "correlation_id", "context"
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    if app_filter:
        query["query"]["bool"]["must"].append({"terms": {"app": app_filter}})
    
    path = f"/{index}/_search"
    url = f"{kibana_url}/api/console/proxy?path={path}&method=POST"
    
    return run_curl(url, method="POST", data=query)


def query_trace_detail(kibana_url, date_str, trace_id):
    """查询trace日志详情"""
    index = f"trace-{date_str}"
    
    # 先尝试 _doc API
    path = f"/{index}/_doc/{trace_id}"
    url = f"{kibana_url}/api/console/proxy?path={path}&method=GET"
    result = run_curl(url)
    
    if result and result.get("found"):
        return result
    
    # 备用 _search 查询
    path = f"/{index}/_search"
    url = f"{kibana_url}/api/console/proxy?path={path}&method=POST"
    data = {"query": {"term": {"id": trace_id}}, "size": 10}
    return run_curl(url, method="POST", data=data)


def query_correlation_chain(kibana_url, date_str, correlation_id):
    """查询完整调用链"""
    index = f"action-{date_str}"
    
    query = {
        "query": {"term": {"correlation_id": correlation_id}},
        "size": 100,
        "sort": [{"@timestamp": "asc"}]
    }
    
    path = f"/{index}/_search"
    url = f"{kibana_url}/api/console/proxy?path={path}&method=POST"
    return run_curl(url, method="POST", data=query)


def format_groups_for_agents(agg_result):
    """格式化分组结果为Sub Agent任务列表"""
    groups = []
    
    if not agg_result or "aggregations" not in agg_result:
        return groups
    
    for app_bucket in agg_result["aggregations"]["by_app"]["buckets"]:
        app_name = app_bucket["key"]
        
        for action_bucket in app_bucket["by_action"]["buckets"]:
            action_name = action_bucket["key"]
            
            for error_bucket in action_bucket["by_error"]["buckets"]:
                error_code = error_bucket["key"]
                count = error_bucket["doc_count"]
                sample = error_bucket["sample_hit"]["hits"]["hits"][0]
                
                groups.append({
                    "group_id": f"{app_name}/{action_name}/{error_code}",
                    "app": app_name,
                    "action": action_name,
                    "error_code": error_code,
                    "count": count,
                    "sample_log": sample["_source"],
                    "trace_id": sample["_source"].get("id"),
                    "correlation_id": sample["_source"].get("correlation_id")
                })
    
    return groups


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Kibana日志查询工具")
    parser.add_argument("--kibana-url", required=True, help="Kibana URL")
    parser.add_argument("--date", default=datetime.now().strftime("%Y.%m.%d"), help="日期 (yyyy.mm.dd)")
    parser.add_argument("--hours", type=int, default=1, help="查询最近N小时")
    parser.add_argument("--app", nargs="*", help="过滤特定app")
    parser.add_argument("--mode", choices=["groups", "trace", "chain"], required=True,
                       help="查询模式: groups=分组统计, trace=trace详情, chain=调用链")
    parser.add_argument("--trace-id", help="trace日志ID (trace模式需要)")
    parser.add_argument("--correlation-id", help="调用链ID (chain模式需要)")
    
    args = parser.parse_args()
    
    if args.mode == "groups":
        result = query_error_groups(args.kibana_url, args.date, args.app, args.hours)
        groups = format_groups_for_agents(result)
        print(json.dumps(groups, ensure_ascii=False, indent=2))
    
    elif args.mode == "trace":
        if not args.trace_id:
            print("Error: --trace-id required for trace mode", file=sys.stderr)
            sys.exit(1)
        result = query_trace_detail(args.kibana_url, args.date, args.trace_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.mode == "chain":
        if not args.correlation_id:
            print("Error: --correlation-id required for chain mode", file=sys.stderr)
            sys.exit(1)
        result = query_correlation_chain(args.kibana_url, args.date, args.correlation_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
