# 日志字段 Schema 定义

## 概述

本文档定义 LogScope 处理的日志字段结构，包括 Action 索引和 Trace 索引的字段定义、标准化映射规则，以及双索引查询策略。

## Action 索引字段定义

### 索引名称格式
`action-yyyy.mm.dd`（如 `action-2026.10.10`）

### 核心字段

| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `@timestamp` | date | 时间戳（ISO 8601） | `"2026-10-10T11:17:18.704896811Z"` |
| `id` | keyword | 请求 ID（主键） | `"A1258818F02B8859C9E8"` |
| `app` | keyword | 服务名 | `"report-service"` |
| `host` | keyword | 主机名 | `"report-service-66555d7449-x5t9b"` |
| `result` | keyword | 执行结果 | `"ERROR"` / `"SUCCESS"` |
| `ref_id` | keyword[] | 上游请求引用 ID | `["A1258818EADBFBE7C5BC"]` |
| `correlation_id` | keyword[] | 业务流关联 ID | `["A1258818EADBFBE7C5BC"]` |
| `client` | keyword[] | 客户端标识 | `["merchant-site"]` |
| `action` | keyword | 操作路径 | `"api:put:/bo/report/ads/campaign/summary"` |
| `error_code` | keyword | 错误码 | `"core.framework.db.UncheckedSQLException"` |
| `error_message` | text | 错误消息 | `"Unknown column 'channel' in 'where clause'"` |
| `elapsed` | long | 耗时（纳秒） | `5745546` |

### context 字段

| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `context.controller` | keyword[] | 控制器类名 | `["app.report.web.BOReportWebServiceImpl.getAdsCampaignSummary"]` |
| `context.response_code` | keyword[] | HTTP 响应码 | `["500"]` |
| `context.method` | keyword[] | HTTP 方法 | `["PUT"]` |
| `context.client_ip` | keyword[] | 客户端 IP | `["10.0.66.110"]` |
| `context.merchant_id` | keyword[] | 商户 ID（业务键） | `["d5673e51-9e7b-4e64-957d-767b67df8db7"]` |
| `context.path_pattern` | keyword[] | 路径模式 | `["/bo/report/ads/campaign/summary"]` |
| `context.request_url` | keyword[] | 请求 URL | `["https://report-service/bo/report/ads/campaign/summary"]` |

### stats 字段

| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `stats.response_body_length` | long | 响应体长度 | `2874` |
| `stats.db_queries` | integer | 数据库查询次数 | `1` |
| `stats.http_delay` | long | HTTP 延迟（纳秒） | `182893` |
| `stats.request_body_length` | long | 请求体长度 | `203` |

### perf_stats 字段

| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `perf_stats.db.total_elapsed` | long | 数据库总耗时（纳秒） | `4309781` |
| `perf_stats.db.count` | integer | 数据库调用次数 | `1` |

---

## Trace 索引字段定义

### 索引名称格式
`trace-yyyy.mm.dd`（如 `trace-2026.10.10`）

### 核心字段

| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `@timestamp` | date | 时间戳 | `"2026-10-10T11:17:18.704896811Z"` |
| `_id` | keyword | 文档 ID（等于 action 的 id） | `"A1258818F02B8859C9E8"` |
| `app` | keyword | 服务名 | `"report-service"` |
| `result` | keyword | 执行结果 | `"ERROR"` |
| `action` | keyword | 操作路径 | `"api:put:/bo/report/ads/campaign/summary"` |
| `error_code` | keyword | 错误码 | `"core.framework.db.UncheckedSQLException"` |
| `content` | text | 完整的执行日志（非结构化） | （见下文） |

### content 字段结构

`content` 字段包含完整的执行日志，按时间顺序排列：

1. **HTTP 请求开始标记**
   ```
   00:00.000011812 c.f.i.log.ActionLog - === http begin ===
   ```

2. **请求 ID**
   ```
   00:00.000013135 c.f.i.log.ActionLog - id=A1258818F02B8859C9E8
   ```

3. **时间戳**
   ```
   00:00.000025759 c.f.i.log.ActionLog - date=2026-10-10T11:17:18.704896811Z
   ```

4. **线程信息**
   ```
   00:00.000026330 c.f.i.log.ActionLog - thread=http-handler-5
   ```

5. **HTTP 延迟**
   ```
   00:00.000036509 c.f.i.web.HTTPHandler - httpDelay=182893
   ```

6. **请求信息**
   ```
   00:00.000049724 c.f.i.w.request.RequestParser - [request] method=PUT, requestURL=https://report-service/bo/report/ads/campaign/summary
   ```

7. **请求头**
   ```
   00:00.000054974 c.f.i.w.request.RequestParser - [request:header] accept=application/json
   00:00.000077346 c.f.i.w.request.RequestParser - [request:header] correlation-id=A1258818EADBFBE7C5BC
   00:00.000070433 c.f.i.w.request.RequestParser - [request:header] ref-id=A1258818EADBFBE7C5BC
   ```

8. **请求体**
   ```
   00:00.000104898 c.f.i.w.request.RequestParser - [request] body={"start_date":"2026-07-09","end_date":"2026-10-09","merchant_id":"d5673e51-9e7b-4e64-957d-767b67df8db7"}
   ```

9. **路由信息**
   ```
   00:00.000119155 c.f.i.w.route.Route - pathPattern=/bo/report/ads/campaign/summary
   00:00.000122061 c.f.i.log.ActionLog - action=api:put:/bo/report/ads/campaign/summary
   00:00.000123233 c.f.i.web.HTTPHandler - controller=app.report.web.BOReportWebServiceImpl.getAdsCampaignSummary
   ```

10. **上下文信息**
    ```
    00:00.000425264 c.f.i.log.ActionLog - [context] merchant_id=d5673e51-9e7b-4e64-957d-767b67df8db7
    ```

11. **SQL 查询**
    ```
    00:00.004898034 c.f.i.db.DatabaseImpl - selectOne, sql=SELECT COUNT(*) AS sent_messages FROM ads_campaign_customers WHERE merchant_id = ? AND channel IN (?, ?), params=[d5673e51-..., EMAIL, MOBILE_APP], returnedRows=0, elapsed=4309781
    ```

12. **异常信息**
    ```
    00:00.004912411 ERROR c.f.i.log.LogManager - [core.framework.db.UncheckedSQLException] Unknown column 'channel' in 'where clause', sqlState=42S22, errorCode=1054
    core.framework.db.UncheckedSQLException: Unknown column 'channel' in 'where clause'
        at core.framework.internal.db.DatabaseOperation.selectOne(DatabaseOperation.java:93)
        ...
    Caused by: java.sql.SQLSyntaxErrorException: Unknown column 'channel' in 'where clause'
        at com.mysql.cj.jdbc.exceptions.SQLError.createSQLException(SQLError.java:103)
        ...
    ```

13. **响应信息**
    ```
    00:00.005578651 c.f.i.w.response.ResponseHandler - [response] statusCode=500
    00:00.005585334 c.f.i.w.response.ResponseHandler - [response:header] Content-Type=application/json
    00:00.005654795 c.f.i.w.response.BeanBody - [response] body={"id":"A1258818F02B8859C9E8","severity":"ERROR",...}
    ```

14. **HTTP 请求结束标记**
    ```
    00:00.005746619 c.f.i.log.ActionLog - elapsed=5745546
    00:00.005747450 c.f.i.log.ActionLog - === http end ===
    ```

---

## 标准化日志对象

将 ES 文档映射成内部模型：

```json
{
  "log_id": "action-2026.10.10/_doc/A1258818F02B8859C9E8",
  "id": "A1258818F02B8859C9E8",
  "timestamp": "2026-10-10T11:17:18.704896811Z",
  "service": "report-service",
  "host": "report-service-66555d7449-x5t9b",
  "environment": "dev",
  "level": "ERROR",
  "action": "api:put:/bo/report/ads/campaign/summary",
  "error_code": "core.framework.db.UncheckedSQLException",
  "error_message": "Unknown column 'channel' in 'where clause', sqlState=42S22, errorCode=1054",
  "correlation_id": "A1258818EADBFBE7C5BC",
  "ref_id": "A1258818EADBFBE7C5BC",
  "context": {
    "merchant_id": "d5673e51-9e7b-4e64-957d-767b67df8db7",
    "controller": "app.report.web.BOReportWebServiceImpl.getAdsCampaignSummary",
    "response_code": "500",
    "method": "PUT",
    "client_ip": "10.0.66.110",
    "path_pattern": "/bo/report/ads/campaign/summary",
    "request_url": "https://report-service/bo/report/ads/campaign/summary"
  },
  "elapsed_ns": 5745546,
  "stats": {
    "response_body_length": 2874,
    "db_queries": 1,
    "http_delay": 182893,
    "request_body_length": 203
  },
  "perf_stats": {
    "db": {
      "total_elapsed": 4309781,
      "count": 1
    }
  }
}
```

### 实现注意

- 统一时区使用 UTC 存储，报告可按用户时区显示
- `context` 字段可能是数组或单值，需要按实际 mapping 适配
- 不应对动态字段做无限制的字段发现或高基数字段聚合
- 若字段不存在，标记为 `missing`，不自行推断其值

---

## 双索引关联机制

### 关联字段

**Action 索引的 `id` 字段 = Trace 索引的 `_id` 字段**

示例：
- Action: `{ "_id": "xxx", "_source": { "id": "A1258818F02B8859C9E8" } }`
- Trace: `{ "_id": "A1258818F02B8859C9E8", "_source": { ... } }`

### 查询策略

#### 策略 1：从 Action 定位 Trace（最常用）

```json
// Step 1: 在 action 索引中查找错误日志
GET /action-*/_search
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "result.keyword": "ERROR" } },
        { "term": { "context.merchant_id.keyword": "d5673e51-..." } },
        { "range": { "@timestamp": { "gte": "2026-10-10T00:00:00Z", "lte": "2026-10-10T23:59:59Z" } } }
      ]
    }
  }
}

// Step 2: 使用 action 的 id 在 trace 索引中查找详情
GET /trace-*/_search
{
  "query": {
    "ids": {
      "values": ["A1258818F02B8859C9E8"]
    }
  }
}
```

#### 策略 2：通过 correlation_id 追踪完整业务流

```json
// Step 1: 在 action 索引中查找同一业务流的所有请求
GET /action-*/_search
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "correlation_id.keyword": "A1258818EADBFBE7C5BC" } },
        { "range": { "@timestamp": { "gte": "2026-10-10T00:00:00Z", "lte": "2026-10-10T23:59:59Z" } } }
      ]
    }
  },
  "sort": [{ "@timestamp": "asc" }],
  "size": 1000
}

// Step 2: 批量获取所有错误请求的 trace 详情
GET /trace-*/_search
{
  "query": {
    "ids": {
      "values": ["A1258818F02B8859C9E8", "A1258818EADBFBE7C5BC"]
    }
  }
}
```

#### 策略 3：通过 ref_id 追踪上下游调用

```json
// Step 1: 查找当前请求的上游（通过 ref_id）
GET /action-*/_search
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "id.keyword": "A1258818EADBFBE7C5BC" } }
      ]
    }
  }
}

// Step 2: 查找当前请求的下游（通过 correlation_id）
GET /action-*/_search
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "correlation_id.keyword": "A1258818EADBFBE7C5BC" } },
        { "range": { "@timestamp": { "gte": "2026-10-10T00:00:00Z", "lte": "2026-10-10T23:59:59Z" } } }
      ]
    }
  },
  "sort": [{ "@timestamp": "asc" }]
}
```

---

## Trace Content 解析

### 从 content 提取的关键信息

```json
{
  "request_id": "A1258818F02B8859C9E8",
  "timestamp": "2026-10-10T11:17:18.704896811Z",
  "thread": "http-handler-5",
  "http_delay": 182893,
  "method": "PUT",
  "request_url": "https://report-service/bo/report/ads/campaign/summary",
  "headers": {
    "accept": "application/json",
    "correlation-id": "A1258818EADBFBE7C5BC",
    "ref-id": "A1258818EADBFBE7C5BC"
  },
  "request_body": {
    "start_date": "2026-07-09",
    "end_date": "2026-10-09",
    "merchant_id": "d5673e51-9e7b-4e64-957d-767b67df8db7"
  },
  "sql_queries": [
    {
      "sql": "SELECT COUNT(*) AS sent_messages FROM ads_campaign_customers WHERE merchant_id = ? AND channel IN (?, ?)",
      "params": ["d5673e51-...", "EMAIL", "MOBILE_APP"],
      "returned_rows": 0,
      "elapsed_ns": 4309781
    }
  ],
  "exception": {
    "type": "core.framework.db.UncheckedSQLException",
    "message": "Unknown column 'channel' in 'where clause'",
    "sql_state": "42S22",
    "error_code": 1054,
    "stack_trace": "at core.framework.internal.db.DatabaseOperation.selectOne(...)"
  },
  "response": {
    "status_code": 500,
    "body_length": 2874
  }
}
```

### 解析规则

1. **按行分割** content 字段
2. **正则匹配**关键信息：
   - 请求 ID: `id=([A-F0-9]+)`
   - SQL 查询: `sql=(.+?), params=\[(.*?)\], returnedRows=(\d+), elapsed=(\d+)`
   - 异常: `ERROR \[(.+?)\] (.+), sqlState=(\w+), errorCode=(\d+)`
   - 响应码: `statusCode=(\d+)`

3. **提取堆栈跟踪**：从异常行开始，直到下一个日志行

---

## 重要约束

1. **trace 索引不支持 context.key 直接检索**
   - 必须先在 action 索引中检索，再通过 id 关联到 trace

2. **避免在 trace 索引上进行全文搜索**
   - content 字段是非结构化文本，全文搜索性能差且不准确

3. **优先使用 action 索引**
   - action 索引包含所有请求，且支持结构化查询
   - 仅在需要详情时查询 trace

4. **使用 ids 查询批量获取 trace**
   - 避免多次单独查询，提高性能

5. **敏感字段脱敏**
   - merchant_id 等业务键在报告中需要脱敏
   - SQL 参数中的敏感数据需要屏蔽
   - 请求头中的认证信息需要移除
