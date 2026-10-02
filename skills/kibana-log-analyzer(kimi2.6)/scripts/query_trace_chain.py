#!/usr/bin/env python3
"""
Kibana Correlation Chain Query Script

Query action-* index for all logs sharing the same correlation_id
to reconstruct the distributed call chain.

Usage:
    python query_trace_chain.py <kibana_url> <index_date> <correlation_id>

Args:
    kibana_url      - Kibana base URL (e.g., http://kibana:5601)
    index_date      - Index suffix date, e.g., 2026.04.17 or wildcard *
    correlation_id  - The correlation_id to trace

Env:
    KIBANA_AUTH     - Optional "user:password" for basic auth
"""

import sys
import os
import json
import urllib.request
import urllib.error
import base64


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
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    kibana_url = sys.argv[1].rstrip("/")
    index_date = sys.argv[2]
    correlation_id = sys.argv[3]
    auth = os.environ.get("KIBANA_AUTH")

    index_name = f"action-{index_date}"
    proxy_url = f"{kibana_url}/api/console/proxy?path=%2F{index_name}%2F_search&method=GET"

    dsl = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"correlation_id": correlation_id}}
                ]
            }
        },
        "sort": [{"@timestamp": {"order": "asc"}}],
        "size": 500,
        "_source": [
            "id", "@timestamp", "app", "action", "result",
            "error_code", "error_message", "ref_id", "correlation_id", "context"
        ]
    }
    payload = json.dumps(dsl).encode("utf-8")
    result = do_request(proxy_url, data=payload, auth=auth)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
