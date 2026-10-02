# Kibana DSL Query Templates

## 1. Error Log Grouping (Primary)

Group ERROR logs by `app` → `action` → `error_code`, returning one sample per group.

```json
{
  "query": {
    "bool": {
      "must": [
        { "terms": { "app": ["${APP_NAME}"] } },
        { "term": { "result": "ERROR" } },
        { "range": { "@timestamp": { "gte": "now-1h" } } }
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
            "by_error": {
              "terms": { "field": "error_code", "size": 50 },
              "aggs": {
                "sample_hit": {
                  "top_hits": {
                    "size": 1,
                    "sort": [{ "@timestamp": "desc" }],
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
```

## 2. Trace Detail by ID

### Option A: _doc API (preferred)
```bash
curl -s -X GET "${KIBANA_URL}/api/console/proxy?path=%2Ftrace-{date}%2F_doc%2F{trace_id}&method=GET"
```

### Option B: _search fallback (if _doc returns 404)
```bash
curl -s -X POST "${KIBANA_URL}/api/console/proxy?path=%2Ftrace-{date}%2F_search&method=GET" \
  -H "Content-Type: application/json" \
  -d '{"query": {"term": {"id": "{trace_id}"}}, "size": 10}'
```

## 3. Correlation Chain Query

Fetch all logs in a distributed call chain.

```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "correlation_id": "${CORRELATION_ID}" } }
      ]
    }
  },
  "sort": [{ "@timestamp": { "order": "asc" } }],
  "size": 500,
  "_source": [
    "id", "@timestamp", "app", "action", "result",
    "error_code", "error_message", "ref_id", "correlation_id", "context"
  ]
}
```

## 4. Recent Errors by App

Simple list of recent ERROR logs for a specific app.

```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "app": "${APP_NAME}" } },
        { "term": { "result": "ERROR" } },
        { "range": { "@timestamp": { "gte": "now-1h" } } }
      ]
    }
  },
  "sort": [{ "@timestamp": { "order": "desc" } }],
  "size": 50,
  "_source": [
    "id", "@timestamp", "app", "action",
    "error_code", "error_message", "correlation_id"
  ]
}
```

## 5. Error Trend Aggregation

Count errors per 5-minute bucket for trend visualization.

```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "result": "ERROR" } },
        { "range": { "@timestamp": { "gte": "now-1h" } } }
      ]
    }
  },
  "size": 0,
  "aggs": {
    "errors_over_time": {
      "date_histogram": {
        "field": "@timestamp",
        "fixed_interval": "5m"
      },
      "aggs": {
        "by_app": {
          "terms": { "field": "app", "size": 20 }
        }
      }
    }
  }
}
```
