# 关联与引用规则

## 概述

定义 `correlation_id`、`ref_id` 和业务键的关联策略，用于构建跨服务事件时间线和调用链。

## 核心关联字段

### 1. correlation_id（业务流关联）

**用途**：关联同一业务请求或业务流程中的所有日志。

**特点**：
- 同一业务流中的所有请求共享相同的 `correlation_id`
- 用于追踪跨服务的完整调用链
- 在 action 索引中是数组类型（`keyword[]`）

**查询策略**：
```json
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

**约束**：
- 限定时间窗（默认 ±30 分钟）
- 如同一 ID 跨天或重复使用，应进一步按时间和 trace/span 等字段去重
- 结果数量上限：1000 条

### 2. ref_id（上游引用）

**用途**：追踪上下游调用、消息传递或业务对象之间的引用关系。

**特点**：
- 指向触发当前请求的上游请求 ID
- 用于构建调用链的父子关系
- 在 action 索引中是数组类型（`keyword[]`）

**查询策略**：
```json
// 查找上游请求
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

**约束**：
- 使用 visited 集合防止循环引用
- 最大深度：5 层
- 最大日志数量：500 条
- 设置时间窗限制

**关系类型**：
- `ref_upstream`：当前请求的上游
- `ref_downstream`：当前请求的下游（通过 correlation_id 查找）

### 3. context.key（业务键）

**用途**：通过业务上下文中的键定位相关日志。

**常用业务键**：
- `context.merchant_id`：商户 ID
- `context.order_id`：订单 ID
- `context.user_id`：用户 ID
- `context.task_id`：任务 ID

**查询策略**：
```json
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

**约束**：
- 仅使用白名单字段路径
- 必须使用 keyword 类型或 `.keyword` 子字段
- 不得把任意用户字符串直接拼进查询表达式
- 优先使用精确匹配

## 关联优先级

按以下顺序进行关联：

1. **correlation_id**（最高优先级）
   - 关联同一业务流的所有请求
   - 构建完整的时间线

2. **ref_id**（中等优先级）
   - 追踪上下游调用关系
   - 构建调用链图

3. **业务键**（较低优先级）
   - 查找同一业务实体的相关日志
   - 用于扩展调查范围

## 关系边记录

每条关系边必须记录：

```json
{
  "source_evidence_id": "ev-log-002",
  "target_evidence_id": "ev-log-001",
  "relation_type": "ref_upstream",
  "matched_field": "ref_id",
  "matched_value": "A1258818EADBFBE7C5BC",
  "confidence": "high"
}
```

**关系类型**：
- `same_correlation`：同一 correlation_id
- `ref_upstream`：ref_id 指向的上游
- `ref_downstream`：通过 correlation_id 找到的下游
- `business_key`：通过业务键关联
- `heuristic`：启发式关联（基于时间、服务等）

**置信度**：
- `high`：明确的字段匹配（如 correlation_id、ref_id）
- `medium`：业务键匹配
- `low`：启发式关联（仅基于时间相近）

## 循环检测

### 算法

1. 维护 visited 集合（已访问的 ID）
2. 对每个新发现的日志：
   - 检查其 ID 是否在 visited 集合中
   - 如果在，标记为循环引用，停止追踪
   - 如果不在，加入 visited 集合，继续追踪其 ref_id

### 约束

- 最大深度：5 层
- 最大日志数量：500 条
- 设置时间窗限制

### 循环引用处理

如果发现循环引用：
1. 记录循环关系
2. 停止该路径的追踪
3. 在报告中说明循环引用情况
4. 不影响其他路径的追踪

## 时间线构建

### 步骤

1. 收集所有相关日志
2. 按 `@timestamp` 排序
3. 统一时区（UTC）
4. 标记事件类型：
   - `normal`：正常事件
   - `warning`：警告事件
   - `failure`：失败事件
   - `retry`：重试事件
   - `recovery`：恢复事件
   - `unknown`：未知事件

### 输出

```json
{
  "timeline": [
    {
      "timestamp": "2026-10-10T11:17:18.704Z",
      "service": "upstream-service",
      "event": "发起请求",
      "log_id": "A1258818EADBFBE7C5BC",
      "evidence_id": "ev-log-002",
      "event_kind": "normal"
    },
    {
      "timestamp": "2026-10-10T11:17:18.704Z",
      "service": "report-service",
      "event": "广告报表查询失败",
      "log_id": "A1258818F02B8859C9E8",
      "evidence_id": "ev-log-001",
      "event_kind": "failure"
    }
  ]
}
```

## 重要规则

1. **不得将时间相近直接视为因果关系**
   - 必须有明确的关联字段（correlation_id、ref_id、业务键）

2. **不得因某个服务没有日志就断言该服务没有执行**
   - 可能是日志丢失、采样或索引延迟

3. **不得将日志记录顺序直接视为实际业务执行顺序**
   - 日志记录时间可能晚于实际执行时间

4. **不得删除与初步假设相矛盾的日志**
   - 必须保留所有证据，包括反证

5. **区分直接关联和启发式关联**
   - 直接关联：基于明确的关联字段
   - 启发式关联：基于时间、服务等推测
