# 调查工作流详细定义

## 概述

调查工作流分为 10 个阶段（A-J），从初始错误解析到最终报告生成。每个阶段都有明确的输入、输出、约束和状态记录。

## 阶段 A：解析初始错误

### 目标
提取初始日志的关键字段，建立调查起点。

### 输入
- 初始错误日志 ID、ES `_id`，或 Kibana 查询条件
- 时间范围（默认以异常时间为中心 ±30 分钟）
- 环境/集群/服务范围

### 操作步骤

1. **在 action 索引中定位日志**
   ```
   GET /action-*/_search
   {
     "query": { "ids": { "values": ["<log_id>"] } }
   }
   ```

2. **提取关键字段**
   - `id`：请求 ID（主键）
   - `@timestamp`：时间戳
   - `app`：服务名
   - `host`：主机名
   - `result`：执行结果（SUCCESS/ERROR）
   - `action`：操作路径
   - `error_code`：错误码
   - `error_message`：错误消息
   - `correlation_id`：业务流关联 ID
   - `ref_id`：上游请求引用 ID
   - `context`：业务上下文
   - `elapsed`：耗时（纳秒）
   - `stats`：统计信息
   - `perf_stats`：性能统计

3. **标准化为内部日志对象**
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
     "error_message": "Unknown column 'channel' in 'where clause'",
     "correlation_id": "A1258818EADBFBE7C5BC",
     "ref_id": "A1258818EADBFBE7C5BC",
     "context": {
       "merchant_id": "d5673e51-9e7b-4e64-957d-767b67df8db7",
       "controller": "app.report.web.BOReportWebServiceImpl.getAdsCampaignSummary"
     },
     "elapsed_ns": 5745546
   }
   ```

4. **标记为证据**
   ```json
   {
     "evidence_id": "ev-log-001",
     "evidence_type": "log",
     "source": "action-2026.10.10",
     "document_id": "A1258818F02B8859C9E8",
     "observed_at": "2026-10-10T11:17:18.704896811Z",
     "queried_at": "2026-10-10T11:20:00Z",
     "status": "completed"
   }
   ```

### 约束
- 若字段不存在，标记为 `missing`，不自行推断其值
- 将原始日志保留为证据，不对其进行不可逆改写
- 记录查询时间、索引、文档 ID

### 输出
- 标准化日志对象
- 初始证据（ev-log-001）
- 阶段状态：`completed` 或 `failed`

---

## 阶段 B：同业务流扩展

### 目标
根据 `correlation_id` 构建同一业务流的时间线。

### 输入
- 初始日志的 `correlation_id`
- 初始日志的 `@timestamp`
- 时间窗（默认 ±30 分钟）

### 操作步骤

1. **查询同一业务流**
   ```
   GET /action-*/_search
   {
     "query": {
       "bool": {
         "filter": [
           { "term": { "correlation_id.keyword": "A1258818EADBFBE7C5BC" } },
           { "range": { "@timestamp": { "gte": "...", "lte": "..." } } }
         ]
       }
     },
     "sort": [{ "@timestamp": "asc" }],
     "size": 1000
   }
   ```

2. **生成时间线**
   ```json
   {
     "timeline": [
       {
         "timestamp": "2026-10-10T11:17:18.704Z",
         "service": "report-service",
         "event": "广告报表查询",
         "log_id": "A1258818F02B8859C9E8",
         "evidence_id": "ev-log-001",
         "event_kind": "failure"
       }
     ]
   }
   ```

3. **检查查询状态**
   - 结果数量是否达到上限（1000）
   - 查询是否超时
   - 索引是否覆盖所需时间范围

### 约束
- 结果数量上限：1000 条
- 查询超时限制：30 秒
- 如同一 ID 跨天或重复使用，应进一步按时间和 trace/span 等字段去重

### 输出
- 时间线列表
- 检索状态（completed/partial/failed/timeout）
- 日志数量

---

## 阶段 C：上下游追踪

### 目标
沿 `ref_id` 追踪上下游调用关系。

### 输入
- 当前日志的 `ref_id`
- visited 集合（防止循环）

### 操作步骤

1. **查找上游请求**
   ```
   GET /action-*/_search
   {
     "query": {
       "bool": {
         "filter": [
           { "term": { "id.keyword": "<ref_id>" } }
         ]
       }
     }
   }
   ```

2. **递归追踪**（最大深度 5 层）
   - 对每个新发现的日志，检查其 `ref_id`
   - 如果 `ref_id` 不在 visited 集合中，继续追踪
   - 将已访问的 ID 加入 visited 集合

3. **记录关系边**
   ```json
   {
     "relations": [
       {
         "source_evidence_id": "ev-log-002",
         "target_evidence_id": "ev-log-001",
         "relation_type": "ref_upstream",
         "matched_field": "ref_id",
         "confidence": "high"
       }
     ]
   }
   ```

### 约束
- 使用 visited 集合防止循环引用
- 最大深度：5 层
- 最大日志数量：500 条
- 设置时间窗限制

### 输出
- 调用链图
- 关系列表
- 循环检测结果

---

## 阶段 D：业务键检索

### 目标
根据业务上下文中的键定位相关日志。

### 输入
- 初始日志的 `context` 字段
- 业务键白名单（如 `merchant_id`、`order_id`）

### 操作步骤

1. **提取业务键**
   ```json
   {
     "field": "context.merchant_id",
     "value": "d5673e51-9e7b-4e64-957d-767b67df8db7"
   }
   ```

2. **查询相关日志**
   ```
   GET /action-*/_search
   {
     "query": {
       "bool": {
         "filter": [
           { "term": { "context.merchant_id.keyword": "d5673e51-..." } },
           { "range": { "@timestamp": { "gte": "...", "lte": "..." } } }
         ]
       }
     },
     "size": 500
   }
   ```

3. **记录匹配数量**

### 约束
- 仅使用白名单字段路径
- 优先使用 keyword 类型或 `.keyword` 子字段
- 不得把任意用户字符串直接拼进查询表达式

### 输出
- 相关日志列表
- 匹配数量
- 截断状态

---

## 阶段 E：定位 Trace 详情

### 目标
获取异常请求的详细执行过程。

### 输入
- action 日志的 `id` 字段

### 操作步骤

1. **查询 trace 索引**
   ```
   GET /trace-*/_search
   {
     "query": {
       "ids": { "values": ["A1258818F02B8859C9E8"] }
     }
   }
   ```

2. **解析 content 字段**
   提取以下信息：
   - HTTP 请求信息（method, URL, headers, body）
   - 路由信息（pathPattern, controller）
   - SQL 查询（语句、参数、返回行数、耗时）
   - 异常堆栈（完整的 Java stack trace）
   - HTTP 响应信息（status code, headers, body）

3. **结构化为内部对象**
   ```json
   {
     "request_id": "A1258818F02B8859C9E8",
     "timestamp": "2026-10-10T11:17:18.704896811Z",
     "method": "PUT",
     "request_url": "https://report-service/bo/report/ads/campaign/summary",
     "sql_queries": [
       {
         "sql": "SELECT COUNT(*) FROM ads_campaign_customers WHERE ...",
         "params": ["d5673e51-...", "EMAIL", "MOBILE_APP"],
         "returned_rows": 0,
         "elapsed_ns": 4309781
       }
     ],
     "exception": {
       "type": "core.framework.db.UncheckedSQLException",
       "message": "Unknown column 'channel' in 'where clause'",
       "sql_state": "42S22",
       "error_code": 1054
     },
     "response": {
       "status_code": 500
     }
   }
   ```

4. **标记为证据**

### 约束
- trace 索引不支持 context.key 直接检索
- 避免在 trace 索引上进行全文搜索
- 使用 `ids` 查询批量获取 trace

### 输出
- 结构化的 trace 信息
- SQL 查询列表
- 异常堆栈
- 证据列表

---

## 阶段 F：建立假设

### 目标
基于日志时间线形成可证伪的根因假设。

### 输入
- 日志时间线
- 异常信息
- SQL 查询结果

### 操作步骤

1. **生成假设**
   ```json
   {
     "hypothesis_id": "H-DATA-001",
     "category": "data_error",
     "statement": "SQL 查询引用了不存在的列 'channel'，导致语法错误",
     "status": "supported",
     "confidence": "high",
     "supporting_evidence": ["ev-log-001", "ev-trace-001"],
     "counter_evidence": [],
     "missing_evidence": [],
     "next_action": "检查数据库 schema 确认 channel 列是否存在"
   }
   ```

2. **为每个假设分配验证计划**

### 约束
- 优先调查能解释最多关键现象的假设
- 禁止为了"找到根因"而只搜寻支持某个假设的证据

### 输出
- 假设列表
- 每个假设的验证计划

---

## 阶段 G：数据库验证

### 目标
通过只读查询验证数据层假设。

### 输入
- 待验证的假设
- 业务键和实体类型

### 操作步骤

1. **设计查询**
   ```sql
   SHOW COLUMNS FROM ads_campaign_customers LIKE 'channel';
   ```

2. **执行查询**
   - 记录 `datasource_id`
   - 记录查询状态、耗时、行数、截断标记

3. **交叉验证**
   - 与日志时间线对比
   - 检查是否支持或反驳假设

### 约束
- 仅执行只读查询
- 区分 `primary_datasource_id` 和 `datasource_id`
- `no_rows` 不等于"数据不存在"

### 输出
- 查询结果
- 证据列表
- 数据源状态

---

## 阶段 H：综合与分类

### 目标
综合所有证据，形成最终根因判断。

### 输入
- 所有证据
- 已验证的假设
- 数据库查询结果

### 操作步骤

1. **按时间线建立事件顺序**
2. **区分最早异常、直接错误、后续连锁异常**
3. **选择根因分类**
4. **评估置信度**
5. **生成因果链**
   ```json
   {
     "causal_chain": [
       {
         "step": 1,
         "description": "SQL 查询引用了不存在的列 'channel'",
         "evidence_ids": ["ev-log-001", "ev-trace-001", "ev-sql-001"]
       },
       {
         "step": 2,
         "description": "MySQL 返回语法错误（sqlState=42S22）",
         "evidence_ids": ["ev-trace-001"]
       },
       {
         "step": 3,
         "description": "应用抛出 UncheckedSQLException",
         "evidence_ids": ["ev-log-001"]
       },
       {
         "step": 4,
         "description": "HTTP 响应返回 500 错误",
         "evidence_ids": ["ev-log-001"]
       }
     ]
   }
   ```

### 输出
- 根因分类
- 置信度
- 因果链
- 未解决问题

---

## 阶段 I：报告生成

### 目标
生成 HTML 报告和 JSON 摘要。

### 输入
- 调查结果
- 证据索引
- 数据源状态

### 操作步骤

1. **使用模板渲染 HTML 报告**
2. **对所有动态内容进行 HTML escaping**
3. **脱敏敏感字段**
4. **执行最终质量检查**

### 输出
- HTML 报告
- JSON 摘要

---

## 阶段 J：最终审查

### 目标
在报告交付前发现无证据结论、数据解释错误和安全问题。

### 操作步骤

逐项检查 14 个审查点（参见 SKILL.md 阶段 J）。

### 输出
- 审查状态（passed/passed_with_warnings/failed）
- 问题列表
- 建议修正

---

## 调查状态模型

### 整体调查状态
- `completed`：调查已结束，结论和限制已整理
- `partial`：调查已取得部分证据，但关键范围未完成
- `blocked`：权限或关键工具限制导致无法继续
- `failed`：调查流程发生无法恢复的错误

### 阶段状态
- `not_started`
- `running`
- `completed`
- `partial`
- `failed`
- `skipped`
- `not_authorized`
