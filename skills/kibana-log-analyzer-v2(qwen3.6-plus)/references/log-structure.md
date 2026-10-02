# Kibana 日志结构详细说明

## 索引结构

### 索引命名规则
- **动态索引**: `action-*`, `trace-*` (通配符匹配所有日期)
- **固定日期索引**: `action-yyyy.mm.dd`, `trace-yyyy.mm.dd`
- **示例**: `action-2026.04.17`, `trace-2026.04.17`

### 索引用途
| 索引 | 用途 | 特点 |
|------|------|------|
| action-* | 基础日志信息 | 包含调用链字段 (ref_id, correlation_id) |
| trace-* | 详细日志信息 | 包含完整错误堆栈 (content) |

## 字段详细说明

### action-* 索引字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| id | string | 日志记录唯一ID | "log-12345-abcde" |
| @timestamp | datetime | 日志时间戳 (ISO 8601) | "2026-04-17T10:30:00.000Z" |
| app | string | 微服务模块名称 | "payment-service", "order-service" |
| action | string | 操作/方法名 | "createOrder", "processPayment" |
| result | string | 日志等级: OK, INFO, WARN, ERROR | "ERROR" |
| error_code | string | 错误编码 | "PAYMENT_TIMEOUT", "DB_CONNECTION_FAILED" |
| ref_id | string | 调用链中上级日志的ID | "log-12344-abcde" |
| correlation_id | string | 调用链链路ID (串联整个调用链) | "corr-67890-fghij" |
| error_message | string | 简短的错误信息 | "支付超时,请稍后重试" |
| context.* | object | 自定义业务上下文 | context.product_id, context.order_id, context.customer_email |

### trace-* 索引字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| id | string | 日志记录唯一ID (与action-*相同) | "log-12345-abcde" |
| @timestamp | datetime | 日志时间戳 (与action-*相同) | "2026-04-17T10:30:00.000Z" |
| app | string | 微服务模块名称 (与action-*相同) | "payment-service" |
| action | string | 操作/方法名 (与action-*相同) | "processPayment" |
| result | string | 日志等级 (与action-*相同) | "ERROR" |
| error_code | string | 错误编码 (与action-*相同) | "PAYMENT_TIMEOUT" |
| content | string | 日志错误详情 (完整堆栈) | "java.lang.RuntimeException: ...\n\tat com.example..." |

## 字段关系图

```
action-* 索引                          trace-* 索引
┌─────────────────────┐               ┌─────────────────────┐
│ id: log-12345       │◄──相同id──────►│ id: log-12345       │
│ @timestamp: 10:30   │◄──相同时间────►│ @timestamp: 10:30   │
│ app: payment        │◄──相同服务────►│ app: payment        │
│ action: pay         │◄──相同操作────►│ action: pay         │
│ result: ERROR       │◄──相同等级────►│ result: ERROR       │
│ error_code: TIMEOUT │◄──相同错误────►│ error_code: TIMEOUT │
│ ref_id: log-12344   │               │ content: 完整堆栈   │
│ correlation_id: c-1 │               └─────────────────────┘
│ error_message: 超时 │
│ context: {订单号}   │
└─────────────────────┘
```

## 调用链追踪逻辑

### correlation_id 的作用
- **唯一标识一次完整的请求链路**
- 从网关入口到最底层服务的所有日志都共享同一个 correlation_id
- 通过 correlation_id 可以还原完整的调用链时间线

### ref_id 的作用
- **标识当前日志的父级日志**
- 形成树状调用结构: ref_id → 父日志 id → 祖父日志 id
- 用于追踪方法调用层级关系

### 调用链查询示例
```bash
# 查询完整调用链
curl -s -X POST "${KIBANA_URL}/api/console/proxy?path=%2Faction-{date}%2F_search&method=POST" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {"term": {"correlation_id": "corr-xxx"}},
    "size": 100,
    "sort": [{"@timestamp": "asc"}]
  }'
```

## 常见错误模式

### 1. 数据库相关错误
- **DB_CONNECTION_FAILED**: 数据库连接失败
- **DB_TIMEOUT**: 数据库查询超时
- **DB_DEADLOCK**: 数据库死锁
- **DB_CONSTRAINT_VIOLATION**: 数据库约束违反

### 2. 外部服务调用错误
- **HTTP_TIMEOUT**: HTTP请求超时
- **HTTP_5XX**: 下游服务5xx错误
- **RPC_FAILED**: RPC调用失败
- **SERVICE_UNAVAILABLE**: 服务不可用

### 3. 业务逻辑错误
- **VALIDATION_FAILED**: 参数校验失败
- **BUSINESS_RULE_VIOLATION**: 业务规则违反
- **INSUFFICIENT_PERMISSION**: 权限不足
- **RESOURCE_NOT_FOUND**: 资源不存在

### 4. 系统级错误
- **OUT_OF_MEMORY**: 内存溢出
- **THREAD_POOL_EXHAUSTED**: 线程池耗尽
- **DISK_FULL**: 磁盘空间不足
- **CONFIG_ERROR**: 配置错误

## 根因分析指南

### 分析步骤

1. **定位错误类型**
   - 根据 error_code 判断错误大类
   - 根据 app 和 action 判断出错模块

2. **查看trace详情**
   - 读取 content 字段的完整堆栈
   - 识别异常类型和出错代码行
   - 注意异常链 (caused by)

3. **追踪调用链**
   - 通过 correlation_id 获取完整调用链
   - 按时间戳排序还原调用顺序
   - 识别第一个出错的节点

4. **分析业务上下文**
   - 检查 context 中的业务参数
   - 判断是否是特定数据触发的问题
   - 识别是否是并发/竞态条件

5. **推断根本原因**
   - **不要停留在表面错误** (如 "NullPointerException")
   - **深入分析为什么会出现这个错误**
   - **考虑是否是设计缺陷、配置问题、还是数据异常**

### 根因分析示例

**表面错误**: `NullPointerException at OrderService.java:123`

**根因分析**:
```
1. 直接原因: order.getProduct() 返回 null
2. 为什么为null: 订单创建时未正确关联产品
3. 根本原因: 
   - 场景A: 并发创建订单时,产品被删除 (竞态条件)
   - 场景B: 历史数据迁移时丢失了产品关联 (数据完整性问题)
   - 场景C: 产品删除时未检查订单引用 (设计缺陷)
```

## 影响等级评估标准

### P0 - 紧急 (Critical)
- **条件**: count > 100 或 核心服务 (order/payment/user/auth)
- **特征**: 
  - 影响核心业务流程
  - 大量用户受影响
  - 可能导致数据不一致
- **响应**: 立即修复,必要时回滚

### P1 - 高 (High)
- **条件**: count > 50 或 重要服务
- **特征**:
  - 影响重要功能
  - 部分用户受影响
  - 有降级方案但不理想
- **响应**: 当天内修复

### P2 - 中 (Medium)
- **条件**: count > 10
- **特征**:
  - 影响非核心功能
  - 少量用户受影响
  - 有明确的绕过方案
- **响应**: 本周内修复

### P3 - 低 (Low)
- **条件**: count <= 10
- **特征**:
  - 边缘场景触发
  - 极少数用户受影响
  - 不影响主要业务流程
- **响应**: 排期修复

## 查询性能优化建议

1. **使用固定日期索引** 而非通配符索引 (如 `action-2026.04.17` 而非 `action-*`)
2. **限制时间范围** 避免全表扫描
3. **使用 aggregation** 而非多次单条查询
4. **合理设置 size** 避免返回过多数据
