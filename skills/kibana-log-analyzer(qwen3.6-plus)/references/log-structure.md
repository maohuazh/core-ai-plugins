# Kibana日志分析参考文档

## 索引结构

### action-* 索引
存放日志基础信息和调用链元数据

**主要字段**:
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 日志记录唯一ID |
| @timestamp | datetime | 日志时间戳 |
| app | string | 微服务模块名称 |
| action | string | 操作/方法名称 |
| result | string | 日志等级: OK, INFO, WARN, ERROR |
| error_code | string | 错误编码 |
| ref_id | string | 上级日志ID (调用链父节点) |
| correlation_id | string | 调用链链路ID (串联整个调用链) |
| error_message | string | 简短错误信息 |
| context.* | object | 业务自定义字段 (如 product_id, order_id, customer_email) |

### trace-* 索引
存放详细日志内容和错误堆栈

**主要字段**:
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 日志记录唯一ID (与action-*索引相同) |
| @timestamp | datetime | 日志时间戳 |
| app | string | 微服务模块名称 |
| action | string | 操作/方法名称 |
| result | string | 日志等级 |
| error_code | string | 错误编码 |
| content | text | 日志错误详情 (堆栈跟踪、详细错误信息) |

## 索引命名规则

- 通配符索引: `action-*`, `trace-*`
- 固定日期索引: `action-yyyy.mm.dd`, `trace-yyyy.mm.dd`
- 示例: `action-2026.04.17`, `trace-2026.04.17`

## 调用链追踪机制

### correlation_id
- 一次完整请求的唯一标识
- 可以串联该请求下的所有日志记录
- 仅存在于 action-* 索引

### ref_id
- 指向调用链中上级日志的ID
- 用于构建调用树结构
- 仅存在于 action-* 索引

### 调用链查询示例
```json
{
  "query": {"term": {"correlation_id": "xxx-xxx-xxx"}},
  "sort": [{"@timestamp": "asc"}]
}
```

## 常见错误模式

### 1. 数据库相关
- `DB_QUERY_TIMEOUT`: 数据库查询超时
- `DB_CONNECTION_REFUSED`: 数据库连接拒绝
- `DEADLOCK_FOUND`: 死锁检测

### 2. 外部服务调用
- `HTTP_TIMEOUT`: HTTP请求超时
- `HTTP_5XX`: 下游服务5xx错误
- `SERVICE_UNAVAILABLE`: 服务不可用

### 3. 业务逻辑
- `VALIDATION_FAILED`: 参数校验失败
- `BUSINESS_RULE_VIOLATION`: 业务规则违反
- `RESOURCE_NOT_FOUND`: 资源不存在

### 4. 系统异常
- `NULL_POINTER`: 空指针异常
- `OUT_OF_MEMORY`: 内存溢出
- `STACK_OVERFLOW`: 栈溢出

## 根因分析指南

### 分析步骤
1. **定位错误分组**: 按 app/action/error_code 分组
2. **获取样本日志**: 每组取最新一条日志
3. **查询trace详情**: 通过 id 获取 content 字段
4. **追踪调用链**: 通过 correlation_id 获取完整链路
5. **结合源码**: 根据 app + action 定位源码位置
6. **推断根因**: 分析错误堆栈、上下文、调用关系

### 影响评估维度
- **影响范围**: 受影响用户数、订单数、金额
- **影响等级**: 
  - P0: 核心功能完全不可用
  - P1: 核心功能部分受损
  - P2: 非核心功能异常
  - P3: 轻微异常，不影响主流程

### 修复建议分类
- **紧急修复**: 立即修复的bug
- **优化建议**: 代码质量、性能优化
- **架构改进**: 系统架构层面的优化
- **监控增强**: 增加监控告警
