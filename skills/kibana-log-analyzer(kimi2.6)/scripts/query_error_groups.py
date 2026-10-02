#!/usr/bin/env python3
"""
Kibana Error Log Grouping Query Script

Query action-* index for ERROR logs grouped by app, action, error_code.
Output JSON with one sample hit per group.

Usage:
    python query_error_groups.py <kibana_url> <index_date> [app_filter] [time_range]

Args:
    kibana_url   - Kibana base URL (e.g., http://kibana:5601)
    index_date   - Index suffix date, e.g., 2026.04.17 or wildcard *
    app_filter   - Optional comma-separated app names to filter
    time_range   - Optional time range, default "now-1h". e.g. "now-24h"

Env:
    KIBANA_AUTH  - Optional "user:password" for basic auth
"""

import sys
import os
import json
import urllib.request
import urllib.error
import base64


def build_dsl(app_filter=None, time_range="now-1h"):
    must_clauses = [
        {"term": {"result": "ERROR"}},
        {"range": {"@timestamp": {"gte": time_range}}}
    ]
    if app_filter:
        apps = [a.strip() for a in app_filter.split(",") if a.strip()]
        if apps:
            must_clauses.insert(0, {"terms": {"app": apps}})

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
                                                "error_code", "error_message", "ref_id",
                                                "correlation_id", "context"
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
    return dsl


def do_request(url, data=None, headers=None, auth=None):
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    if auth:
        token = base64.b64encode(auth.encode("utf-8")).decode("utf-8")
        req_headers["Authorization"] = f"Basic {token}"

    req = urllib.request.Request(url, data=data, headers=req_headers, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        return {"_http_error": True, "status": e.code, "body": body}
    except Exception as e:
        return {"_error": True, "message": str(e)}


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    kibana_url = sys.argv[1].rstrip("/")
    index_date = sys.argv[2]
    app_filter = sys.argv[3] if len(sys.argv) > 3 else None
    time_range = sys.argv[4] if len(sys.argv) > 4 else "now-1h"

    index_name = f"action-{index_date}"
    proxy_url = f"{kibana_url}/api/console/proxy?path=%2F{index_name}%2F_search&method=GET"

    dsl = build_dsl(app_filter, time_range)
    payload = json.dumps(dsl).encode("utf-8")

    auth = os.environ.get("KIBANA_AUTH")
    result = do_request(proxy_url, data=payload, auth=auth)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
