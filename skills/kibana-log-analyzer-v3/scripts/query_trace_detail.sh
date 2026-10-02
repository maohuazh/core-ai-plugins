#!/bin/bash
# 查询 Trace 详细日志
# 用法: ./query_trace_detail.sh <kibana_url> <date> <trace_id>

KIBANA_URL="${1:-$KIBANA_URL}"
DATE="${2}"
TRACE_ID="${3}"

INDEX="trace-${DATE}"

# 首先尝试 _doc API
RESPONSE=$(curl -s -X GET "${KIBANA_URL}/api/console/proxy?path=%2F${INDEX}%2F_doc%2F${TRACE_ID}&method=GET")

# 检查是否返回 404 或错误
if echo "$RESPONSE" | grep -q '"found":false'; then
  # 使用 _search 备用查询
  curl -s -X POST "${KIBANA_URL}/api/console/proxy?path=%2F${INDEX}%2F_search&method=GET" \
    -H "Content-Type: application/json" \
    -d "{\"query\": {\"term\": {\"id\": \"${TRACE_ID}\"}}, \"size\": 10}"
else
  echo "$RESPONSE"
fi
