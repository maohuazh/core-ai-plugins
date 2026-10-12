# LogScope 日志结构分析

## 双索引架构

### Action 索引 (action-yyyy.mm.dd)
**用途**: 存储请求的基本信息（结构化数据）
**特点**: 
- 所有请求都有 action index 的日志数据
- 可以直接通过 context.key 检索
- 包含摘要级别的请求信息

**核心字段**:
```json
{
  "@timestamp": "2026-10-10T11:17:18.704896811Z",
  "id": "A1258818F02B8859C9E8",                    // 请求 ID（主键）
  "app": "report-service",                          // 服务名
  "host": "report-service-66555d7449-x5t9b",       // 主机名
  "result": "ERROR",                                // 执行结果（SUCCESS/ERROR）
  "ref_id": ["A1258818EADBFBE7C5BC"],              // 引用 ID（上游请求）
  "correlation_id": ["A1258818EADBFBE7C5BC"],      // 关联 ID（业务流）
  "client": ["merchant-site"],                      // 客户端
  "action": "api:put:/bo/report/ads/campaign/summary", // 操作路径
  "error_code": "core.framework.db.UncheckedSQLException", // 错误码
  "error_message": "Unknown column 'channel'...",   // 错误消息
  "elapsed": 5745546,                               // 耗时（纳秒）
  
  "context": {                                      // 业务上下文
    "controller": ["app.report.web.BOReportWebServiceImpl.getAdsCampaignSummary"],
    "response_code": ["500"],
    "method": ["PUT"],
    "client_ip": ["10.0.66.110"],
    "merchant_id": ["d5673e51-9e7b-4e64-957d-767b67df8db7"], // 业务键
    "path_pattern": ["/bo/report/ads/campaign/summary"],
    "request_url": ["https://report-service/bo/report/ads/campaign/summary"]
  },
  
  "stats": {                                        // 统计信息
    "response_body_length": 2874,
    "db_queries": 1,                                // 数据库查询次数
    "http_delay": 182893,
    "request_body_length": 203
  },
  
  "perf_stats": {                                   // 性能统计
    "db": {
      "total_elapsed": 4309781,                     // 数据库总耗时
      "count": 1
    }
  }
}
```

### Trace 索引 (trace-yyyy.mm.dd)
**用途**: 存储异常的详细执行过程（非结构化数据）
**特点**:
- 只有包含 error_code 的日志数据才有详情日志
- context.key 不能直接检索到该索引下的日志
- 包含完整的执行轨迹（从 http begin 到 http end）

**核心字段**:
```json
{
  "@timestamp": "2026-10-10T11:17:18.704896811Z",
  "app": "report-service",
  "result": "ERROR",
  "action": "api:put:/bo/report/ads/campaign/summary",
  "error_code": "core.framework.db.UncheckedSQLException",
  "content": "完整的执行日志（包含请求头、请求体、SQL、异常堆栈、响应等）"
}
```

**content 字段结构**（按时间顺序）:
1. HTTP 请求开始标记: `=== http begin ===`
2. 请求 ID: `id=A1258818F02B8859C9E8`
3. 时间戳: `date=2026-10-10T11:17:18.704896811Z`
4. 线程信息: `thread=http-handler-5`
5. HTTP 延迟: `httpDelay=182893`
6. 请求信息: `method=PUT, requestURL=...`
7. 请求头: `[request:header] accept=application/json` 等
8. 请求体: `[request] body={...}`
9. 路由信息: `pathPattern=...`, `action=...`, `controller=...`
10. 上下文信息: `[context] merchant_id=...`
11. **SQL 查询**: `selectOne, sql=SELECT ..., params=[...], returnedRows=0, elapsed=...`
12. **异常信息**: `ERROR [error_code] message\n堆栈跟踪`
13. 响应信息: `[response] statusCode=500`
14. 响应头: `[response:header] Content-Type=application/json`
15. 响应体: `[response] body={...}`
16. HTTP 请求结束标记: `=== http end ===`

## 双索引关联机制

### 关联字段
**Action 索引的 `id` 字段 = Trace 索引的 `_id` 字段**

示例：
- Action: `{ "_id": "xxx", "_source": { "id": "A1258818F02B8859C9E8" } }`
- Trace: `{ "_id": "A1258818F02B8859C9E8", "_source": { ... } }`

### 查询策略

#### 场景 1: 从 Action 定位 Trace
```json
// Step 1: 在 action 索引中查找错误日志
GET /action-*/_search
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "result.keyword": "ERROR" } },
        { "term": { "context.merchant_id.keyword": "d5673e51-9e7b-4e64-957d-767b67df8db7" } },
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

#### 场景 2: 从 Trace 反查 Action
```json
// Step 1: 在 trace 索引中查找错误详情
GET /trace-*/_search
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "error_code.keyword": "core.framework.db.UncheckedSQLException" } },
        { "range": { "@timestamp": { "gte": "2026-10-10T00:00:00Z", "lte": "2026-10-10T23:59:59Z" } } }
      ]
    }
  }
}

// Step 2: 使用 trace 的 _id 在 action 索引中查找基本信息
GET /action-*/_search
{
  "query": {
    "term": { "id.keyword": "A1258818F02B8859C9E8" }
  }
}
```

#### 场景 3: 通过 correlation_id 追踪完整业务流
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
      "values": ["A1258818F02B8859C9E8", "A1258818EADBFBE7C5BC", "..."]
    }
  }
}
```

#### 场景 4: 通过 ref_id 追踪上下游调用
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

## 关键字段映射

### 从 content 字段提取的结构化信息

```javascript
// 从 trace 的 content 字段提取关键信息
function parseTraceContent(content) {
  const result = {
    request_id: null,
    timestamp: null,
    thread: null,
    http_delay: null,
    method: null,
    request_url: null,
    headers: {},
    body: null,
    context: {},
    sql_queries: [],
    exception: null,
    response: null
  };
  
  const lines = content.split('\n');
  for (const line of lines) {
    // 提取请求 ID
    if (line.includes('id=')) {
      result.request_id = line.match(/id=([A-F0-9]+)/)?.[1];
    }
    // 提取时间戳
    else if (line.includes('date=')) {
      result.timestamp = line.match(/date=(.+)/)?.[1];
    }
    // 提取线程
    else if (line.includes('thread=')) {
      result.thread = line.match(/thread=(.+)/)?.[1];
    }
    // 提取 SQL 查询
    else if (line.includes('sql=')) {
      const sqlMatch = line.match(/sql=(.+?), params=\[(.*?)\], returnedRows=(\d+), elapsed=(\d+)/);
      if (sqlMatch) {
        result.sql_queries.push({
          sql: sqlMatch[1],
          params: sqlMatch[2].split(', '),
          returned_rows: parseInt(sqlMatch[3]),
          elapsed_ns: parseInt(sqlMatch[4])
        });
      }
    }
    // 提取异常
    else if (line.includes('ERROR')) {
      result.exception = {
        message: line,
        stack_trace: []
      };
    }
    // 提取响应
    else if (line.includes('[response] statusCode=')) {
      result.response = {
        status_code: line.match(/statusCode=(\d+)/)?.[1]
      };
    }
  }
  
  return result;
}
```

## 日志分析流程

### 阶段 1: 从 Action 索引开始
1. 使用业务键（如 merchant_id）或错误条件在 action 索引中检索
2. 获取请求的基本信息：时间、服务、错误码、耗时等
3. 提取 correlation_id 和 ref_id 用于关联分析

### 阶段 2: 定位 Trace 索引
1. 使用 action 的 id 字段在 trace 索引中查找详情
2. 解析 content 字段，提取：
   - 完整的 HTTP 请求/响应信息
   - SQL 查询语句和参数
   - 异常堆栈跟踪
   - 性能指标（耗时、调用次数等）

### 阶段 3: 关联分析
1. 通过 correlation_id 追踪同一业务流的所有请求
2. 通过 ref_id 追踪上下游调用链
3. 构建完整的事件时间线

### 阶段 4: 根因分析
1. 从 trace 的 content 中提取 SQL 查询和异常信息
2. 分析 SQL 语法错误、业务逻辑错误等
3. 结合数据库查询验证假设
4. 生成根因分类和置信度评估

### 阶段 5: 报告生成
1. 整合 action 和 trace 的信息
2. 生成包含完整证据链的 HTML 报告
3. 包含 SQL 查询、异常堆栈、业务上下文等关键证据

## 安全注意事项

1. **敏感字段脱敏**:
   - merchant_id 等业务键在报告中需要脱敏
   - SQL 参数中的敏感数据需要屏蔽
   - 请求头中的认证信息需要移除

2. **查询限制**:
   - trace 索引不能通过 context.key 直接检索，只能通过 id 关联
   - 避免在 trace 索引上进行全文搜索（性能差）
   - 优先使用 action 索引进行检索，仅在需要详情时查询 trace

3. **性能优化**:
   - 使用 ids 查询批量获取 trace 详情
   - 限制单次查询的时间窗口（默认 ±30 分钟）
   - 限制单次查询的结果数量（默认 1000 条）
