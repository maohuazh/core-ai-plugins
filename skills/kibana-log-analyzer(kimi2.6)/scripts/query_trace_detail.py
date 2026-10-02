#!/usr/bin/env python3
"""
Kibana Trace Log Detail Query Script

Query trace-* index for detailed log content by log id.

Usage:
    python query_trace_detail.py <kibana_url> <index_date> <trace_id>

Args:
    kibana_url   - Kibana base URL (e.g., http://kibana:5601)
    index_date   - Index suffix date, e.g., 2026.04.17
    trace_id     - The log id (same as action-* id)

Env:
    KIBANA_AUTH  - Optional "user:password" for basic auth
"""

import sys
import os
import json
import urllib.request
import urllib.error
import base64


def do_request(url, data=None, headers=None, auth=None, method="GET"):
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    if auth:
        token = base64.b64encode(auth.encode("utf-8")).decode("utf-8")
        req_headers["Authorization"] = f"Basic {token}"

    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        return {"_http_error": True, "status": e.code, "body": body}
    except Exception as e:
        return {"_error": True, "message": str(e)}


def query_by_doc(kibana_url, index_date, trace_id, auth):
    index_name = f"trace-{index_date}"
    url = f"{kibana_url}/api/console/proxy?path=%2F{index_name}%2F_doc%2F{trace_id}&method=GET"
    return do_request(url, auth=auth, method="GET")


def query_by_search(kibana_url, index_date, trace_id, auth):
    index_name = f"trace-{index_date}"
    url = f"{kibana_url}/api/console/proxy?path=%2F{index_name}%2F_search&method=GET"
    dsl = {"query": {"term": {"id": trace_id}}, "size": 10}
    payload = json.dumps(dsl).encode("utf-8")
    return do_request(url, data=payload, auth=auth, method="POST")


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    kibana_url = sys.argv[1].rstrip("/")
    index_date = sys.argv[2]
    trace_id = sys.argv[3]
    auth = os.environ.get("KIBANA_AUTH")

    # Try _doc first
    result = query_by_doc(kibana_url, index_date, trace_id, auth)
    if result.get("_http_error") and result.get("status") == 404:
        # Fallback to _search by id field
        result = query_by_search(kibana_url, index_date, trace_id, auth)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
