# Kibana Index Schema Reference

## Index Naming

| Pattern | Purpose | Example |
|---------|---------|---------|
| `action-*` | Log summary / action records | `action-2026.04.17` |
| `trace-*` | Detailed log content / trace records | `trace-2026.04.17` |

Fixed-date index format: `action-yyyy.mm.dd`, `trace-yyyy.mm.dd`

## action-* Index Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | keyword | Unique log record ID. Shared with trace-* index. |
| `@timestamp` | date | Log timestamp. Shared with trace-* index. |
| `app` | keyword | Microservice module name. Shared with trace-* index. |
| `action` | keyword | Action / operation name. Shared with trace-* index. |
| `result` | keyword | Log level: `OK`, `INFO`, `WARN`, `ERROR`. Shared with trace-* index. |
| `error_code` | keyword | Error code. Shared with trace-* index. |
| `ref_id` | keyword | Parent log ID in the call chain. **action-* only**. |
| `correlation_id` | keyword | Distributed trace link ID. **action-* only**. |
| `error_message` | text | Short error description. **action-* only**. |
| `context.*` | various | Business custom fields. **action-* only**. Examples: `context.product_id`, `context.order_id`, `context.customer_email`. |

## trace-* Index Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | keyword | Unique log record ID. Same value as action-* id. |
| `@timestamp` | date | Log timestamp. |
| `app` | keyword | Microservice module name. |
| `action` | keyword | Action / operation name. |
| `result` | keyword | Log level. |
| `error_code` | keyword | Error code. |
| `content` | text | **Detailed log content / stack trace. trace-* only.** |

## Key Relationships

- **Same `id`** links action-* record to trace-* record.
- **`correlation_id`** links all logs in a distributed call chain across services.
- **`ref_id`** points to the parent log record's `id` within the same chain.
