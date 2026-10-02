# Kibana 日志索引结构

## 索引命名规范

- 基础日志索引：`action-YYYY.MM.DD`（例如：`action-2026.04.17`）
- 详细日志索引：`trace-YYYY.MM.DD`（例如：`trace-2026.04.17`）
- 通配符查询：`action-*`、`trace-*`

## action-* 索引字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | string | 日志记录唯一 ID |
| `@timestamp` | datetime | 日志时间戳 |
| `app` | string | 微服务模块名称 |
| `action` | string | 操作/方法名称 |
| `result` | string | 日志等级：OK, INFO, WARN, ERROR |
| `error_code` | string | 错误编码 |
| `ref_id` | string | 调用链中上级日志的 ID |
| `correlation_id` | string | 调用链链路 ID，可串联整个调用链 |
| `error_message` | string | 简短的错误信息 |
| `context.*` | object | 业务自定义字段，如 `context.product_id`、`context.order_id` |

## trace-* 索引字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | string | 日志记录唯一 ID（与 action-* 相同） |
| `@timestamp` | datetime | 日志时间戳 |
| `app` | string | 微服务模块名称 |
| `action` | string | 操作/方法名称 |
| `result` | string | 日志等级 |
| `error_code` | string | 错误编码 |
| `content` | string | 日志错误详情（堆栈信息、详细错误等） |

## 调用链追踪逻辑

1. `correlation_id` 标识一次完整的请求调用链
2. `ref_id` 指向调用链中的上级日志 ID
3. 通过 `correlation_id` 可以串联同一调用链的所有日志
4. 通过 `ref_id` 可以构建调用树结构

## 常见错误编码规范

错误编码通常遵循以下格式：
- `E001` - 参数校验错误
- `E002` - 业务逻辑错误
- `E003` - 数据库错误
- `E004` - 外部服务调用错误
- `E005` - 系统内部错误

（具体编码规范需根据项目实际情况调整）
