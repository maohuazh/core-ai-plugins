#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kibana 日志查询脚本
支持错误日志分组统计、trace详情查询、调用链查询
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta


def build_headers():
    """构建HTTP请求头"""
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }


def execute_query(kibana_url, path, method='GET', body=None):
    """
    执行Kibana查询
    
    Args:
        kibana_url: Kibana基础URL
        path: Elasticsearch API路径 (如 /action-2026.04.17/_search)
        method: HTTP方法 (GET/POST)
        body: 请求体 (dict)
    
    Returns:
        dict: 查询结果
    """
    # 构建完整的API URL
    encoded_path = urllib.parse.quote(path, safe='')
    url = f"{kibana_url}/api/console/proxy?path={encoded_path}&method={method}"
    
    headers = build_headers()
    data = json.dumps(body).encode('utf-8') if body else None
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP错误: {e.code} - {e.reason}", file=sys.stderr)
        print(f"响应: {e.read().decode('utf-8')}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"查询失败: {e}", file=sys.stderr)
        return None


def query_error_groups(kibana_url, date_str, hours=1, app_filter=None):
    """
    查询错误日志分组统计
    
    Args:
        kibana_url: Kibana基础URL
        date_str: 日期字符串 (格式: yyyy.MM.dd)
        hours: 回溯小时数
        app_filter: 可选的app过滤条件
    
    Returns:
        list: 错误分组列表
    """
    index = f"action-{date_str}"
    
    # 构建查询DSL
    must_clauses = [
        {"term": {"result": "ERROR"}},
        {"range": {"@timestamp": {"gte": f"now-{hours}h"}}}
    ]
    
    if app_filter:
        must_clauses.append({"term": {"app": app_filter}})
    
    dsl = {
        "query": {
            "bool": {
                "must": must_clauses
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
    
    path = f"/{index}/_search"
    result = execute_query(kibana_url, path, method='POST', body=dsl)
    
    if not result or 'aggregations' not in result:
        print("未获取到有效的聚合结果", file=sys.stderr)
        return []
    
    # 解析聚合结果
    groups = []
    by_app = result['aggregations'].get('by_app', {}).get('buckets', [])
    
    for app_bucket in by_app:
        app_name = app_bucket['key']
        by_action = app_bucket.get('by_action', {}).get('buckets', [])
        
        for action_bucket in by_action:
            action_name = action_bucket['key']
            by_error = action_bucket.get('by_error', {}).get('buckets', [])
            
            for error_bucket in by_error:
                error_code = error_bucket['key']
                count = error_bucket['doc_count']
                sample = error_bucket.get('sample_hit', {}).get('hits', {}).get('hits', [{}])[0]
                
                group = {
                    'group_id': f"{app_name}/{action_name}/{error_code}",
                    'app': app_name,
                    'action': action_name,
                    'error_code': error_code,
                    'count': count,
                    'sample_log': sample.get('_source', {}),
                    'trace_id': sample.get('_id', ''),
                    'correlation_id': sample.get('_source', {}).get('correlation_id', '')
                }
                groups.append(group)
    
    return groups


def query_trace_detail(kibana_url, date_str, trace_id):
    """
    查询trace日志详情
    
    Args:
        kibana_url: Kibana基础URL
        date_str: 日期字符串
        trace_id: trace日志ID
    
    Returns:
        dict: trace日志详情
    """
    index = f"trace-{date_str}"
    
    # 优先使用 _doc API
    path = f"/{index}/_doc/{trace_id}"
    result = execute_query(kibana_url, path, method='GET')
    
    if result and result.get('found'):
        return result.get('_source', {})
    
    # 备用 _search 查询
    dsl = {
        "query": {"term": {"id": trace_id}},
        "size": 10
    }
    
    path = f"/{index}/_search"
    result = execute_query(kibana_url, path, method='POST', body=dsl)
    
    if result:
        hits = result.get('hits', {}).get('hits', [])
        if hits:
            return hits[0].get('_source', {})
    
    return {}


def query_correlation_chain(kibana_url, date_str, correlation_id):
    """
    查询完整调用链
    
    Args:
        kibana_url: Kibana基础URL
        date_str: 日期字符串
        correlation_id: 调用链ID
    
    Returns:
        list: 调用链日志列表 (按时间排序)
    """
    if not correlation_id:
        return []
    
    index = f"action-{date_str}"
    
    dsl = {
        "query": {"term": {"correlation_id": correlation_id}},
        "size": 100,
        "sort": [{"@timestamp": "asc"}],
        "_source": [
            "id", "@timestamp", "app", "action", 
            "result", "error_code", "error_message",
            "ref_id", "correlation_id", "context"
        ]
    }
    
    path = f"/{index}/_search"
    result = execute_query(kibana_url, path, method='POST', body=dsl)
    
    if not result:
        return []
    
    hits = result.get('hits', {}).get('hits', [])
    return [hit.get('_source', {}) for hit in hits]


def print_groups(groups):
    """打印分组统计结果"""
    if not groups:
        print("未找到错误日志")
        return
    
    print(f"\n找到 {len(groups)} 个错误分组:\n")
    print(f"{'分组':<50} {'数量':<8}")
    print("-" * 60)
    
    # 按数量排序
    sorted_groups = sorted(groups, key=lambda x: x['count'], reverse=True)
    
    for group in sorted_groups:
        print(f"{group['group_id']:<50} {group['count']:<8}")
    
    print(f"\n总计: {sum(g['count'] for g in groups)} 条错误日志")


def main():
    parser = argparse.ArgumentParser(description='Kibana日志查询工具')
    parser.add_argument('--kibana-url', required=True, help='Kibana URL')
    parser.add_argument('--date', required=True, help='日期 (格式: yyyy.MM.dd)')
    parser.add_argument('--hours', type=int, default=1, help='回溯小时数 (默认: 1)')
    parser.add_argument('--app', help='过滤特定app')
    parser.add_argument('--mode', choices=['groups', 'trace', 'chain'], 
                       default='groups', help='查询模式')
    parser.add_argument('--trace-id', help='trace日志ID (用于trace模式)')
    parser.add_argument('--correlation-id', help='调用链ID (用于chain模式)')
    parser.add_argument('--output', choices=['text', 'json'], default='text',
                       help='输出格式')
    
    args = parser.parse_args()
    
    if args.mode == 'groups':
        groups = query_error_groups(args.kibana_url, args.date, args.hours, args.app)
        
        if args.output == 'json':
            print(json.dumps(groups, indent=2, ensure_ascii=False))
        else:
            print_groups(groups)
    
    elif args.mode == 'trace':
        if not args.trace_id:
            print("错误: trace模式需要指定 --trace-id", file=sys.stderr)
            sys.exit(1)
        
        trace = query_trace_detail(args.kibana_url, args.date, args.trace_id)
        
        if args.output == 'json':
            print(json.dumps(trace, indent=2, ensure_ascii=False))
        else:
            print(f"\nTrace日志详情:")
            print(json.dumps(trace, indent=2, ensure_ascii=False))
    
    elif args.mode == 'chain':
        if not args.correlation_id:
            print("错误: chain模式需要指定 --correlation-id", file=sys.stderr)
            sys.exit(1)
        
        chain = query_correlation_chain(args.kibana_url, args.date, args.correlation_id)
        
        if args.output == 'json':
            print(json.dumps(chain, indent=2, ensure_ascii=False))
        else:
            print(f"\n调用链详情 (共{len(chain)}条日志):")
            for i, log in enumerate(chain, 1):
                print(f"\n[{i}] {log.get('@timestamp', '')} | {log.get('app', '')}/{log.get('action', '')}")
                print(f"    result={log.get('result', '')} error_code={log.get('error_code', '')}")
                if log.get('error_message'):
                    print(f"    error_message={log['error_message']}")


if __name__ == '__main__':
    main()
