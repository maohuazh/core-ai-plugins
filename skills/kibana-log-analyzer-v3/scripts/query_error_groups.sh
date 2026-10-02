#!/bin/bash
# 查询错误日志分组统计
# 用法: ./query_error_groups.sh <kibana_url> <date> [time_range] [app_filter]

KIBANA_URL="${1:-$KIBANA_URL}"
DATE="${2:-$(date +%Y.%m.%d)}"
TIME_RANGE="${3:-1h}"
APP_FILTER="${4:-}"

INDEX="action-${DATE}"

# 构建 DSL
DSL='{
  "query": {
    "bool": {
      "must": [
        { "term": { "result": "ERROR" } },
        { "range": { "@timestamp": { "gte": "now-'${TIME_RANGE}'" } } }
      ]
    }
  },
  "size": 0,
  "aggs": {
    "by_app": {
      "terms": { "field": "app", "size": 50 },
      "aggs": {
        "by_action": {
          "terms": { "field": "action", "size": 50 },
          "aggs": {
            "by_error_code": {
              "terms": { "field": "error_code", "size": 50 },
              "aggs": {
                "sample_log": {
                  "top_hits": {
                    "size": 1,
                    "sort": [{ "@timestamp": "desc" }],
                    "_source": ["id", "@timestamp", "app", "action", "error_code", "error_message", "ref_id", "correlation_id", "path"]
                  }
                },
                "error_count": {
                  "value_count": { "field": "id" }
                }
              }
            }
          }
        }
      }
    }
  }
}'

# 如果指定了 app 过滤
if [ -n "$APP_FILTER" ]; then
  DSL=$(echo "$DSL" | sed 's/"must": \[/"must": [\n        { "terms": { "app": ["'"$APP_FILTER"'"] } },/')
fi

curl -s -X POST "${KIBANA_URL}/api/console/proxy?path=%2F${INDEX}%2F_search&method=GET" \
  -H 'Content-Type: application/json' \
  -d "$DSL"
