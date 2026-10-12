# 证据与置信度规则

## 概述

定义证据引用、置信度评估和假设验证规则，确保每条结论都有可追溯的证据支持。

## 证据数据结构

```json
{
  "evidence_id": "ev-log-001",
  "evidence_type": "log",
  "source": "action-2026.10.10",
  "document_id": "A1258818F02B8859C9E8",
  "observed_at": "2026-10-10T11:17:18.704896811Z",
  "queried_at": "2026-10-10T11:20:00Z",
  "query_summary": "id:A1258818F02B8859C9E8",
  "result_summary": "ERROR: Unknown column 'channel' in 'where clause'",
  "row_count": 1,
  "truncated": false,
  "status": "completed",
  "datasource_id": "es-dev-cluster-01",
  "datasource_role": "primary",
  "freshness_note": "日志索引延迟约 5 秒",
  "hypothesis_ids": ["H-DATA-001"]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `evidence_id` | string | 证据唯一标识（如 ev-log-001, ev-sql-001） |
| `evidence_type` | string | 证据类型：log / sql / mongo / metric / config |
| `source` | string | 数据来源（索引名、数据库名等） |
| `document_id` | string | 文档 ID 或查询 ID |
| `observed_at` | datetime | 观察时间（日志时间戳） |
| `queried_at` | datetime | 查询时间 |
| `query_summary` | string | 查询条件摘要 |
| `result_summary` | string | 结果摘要 |
| `row_count` | integer | 返回行数 |
| `truncated` | boolean | 是否截断 |
| `status` | string | 查询状态：completed / no_rows / denied / timeout / unavailable / truncated |
| `datasource_id` | string | 数据源 ID |
| `datasource_role` | string | 数据源角色：primary / replica / cache |
| `freshness_note` | string | 数据新鲜度说明 |
| `hypothesis_ids` | string[] | 关联的假设 ID 列表 |

### 证据类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `log` | 日志证据 | action 或 trace 索引中的日志 |
| `sql` | SQL 查询结果 | 数据库查询返回的数据 |
| `mongo` | MongoDB 查询结果 | MongoDB 聚合查询返回的数据 |
| `metric` | 监控指标 | CPU、内存、线程池使用率等 |
| `config` | 配置信息 | 应用配置、数据库 schema 等 |

## 证据规则

### 1. 证据必须可追溯

- 每条证据必须有唯一的 `evidence_id`
- 必须记录 `source` 和 `document_id`，便于回查
- 必须记录 `observed_at` 和 `queried_at`，便于验证时效性

### 2. 查询状态必须准确记录

| 状态 | 含义 | 不应得出的结论 |
|------|------|----------------|
| `completed` | 查询成功完成 | - |
| `no_rows` | 查询成功但无结果 | ❌ 数据不存在（可能是查询条件问题） |
| `denied` | 权限拒绝 | ❌ 数据不存在（只是没有权限） |
| `timeout` | 查询超时 | ❌ 数据不存在（只是查询太慢） |
| `unavailable` | 数据源不可用 | ❌ 数据不存在（只是数据源挂了） |
| `truncated` | 结果截断 | ❌ 结果是完整的（只是部分返回） |

### 3. 区分数据源角色

- `primary_datasource_id`：调查主数据源（调查上下文）
- `datasource_id`：当前查询实际执行的数据源
- **重要**：`primary_datasource_id` 不代表自动获得其他数据源权限

### 4. 考虑数据新鲜度

- 记录索引延迟（如"日志索引延迟约 5 秒"）
- 考虑复制延迟（主从延迟）
- 考虑事务隔离（未提交的事务）
- 考虑缓存失效（缓存数据可能过期）

## 假设数据结构

```json
{
  "hypothesis_id": "H-DATA-001",
  "category": "data_error",
  "statement": "SQL 查询引用了不存在的列 'channel'，导致语法错误",
  "status": "supported",
  "confidence": "high",
  "supporting_evidence": ["ev-log-001", "ev-trace-001", "ev-sql-001"],
  "counter_evidence": [],
  "missing_evidence": [],
  "next_action": "检查数据库 schema 确认 channel 列是否存在"
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `hypothesis_id` | string | 假设唯一标识（如 H-DATA-001） |
| `category` | string | 根因分类（参见 root-cause-taxonomy.md） |
| `statement` | string | 可证伪的假设描述 |
| `status` | string | 假设状态：proposed / testing / supported / rejected / inconclusive |
| `confidence` | string | 置信度：high / medium / low / unknown |
| `supporting_evidence` | string[] | 支持证据 ID 列表 |
| `counter_evidence` | string[] | 反证证据 ID 列表 |
| `missing_evidence` | string[] | 缺失证据说明 |
| `next_action` | string | 下一步验证动作 |

### 假设状态

| 状态 | 含义 |
|------|------|
| `proposed` | 已提出，尚未验证 |
| `testing` | 正在验证中 |
| `supported` | 当前证据支持 |
| `rejected` | 有充分证据否定 |
| `inconclusive` | 证据不足或相互冲突 |

## 置信度评估

### 置信度等级

| 等级 | 标识 | 判定标准 | 典型场景 |
|------|------|----------|----------|
| 高 | `high` | 至少有一条直接证据；关键替代解释已排除；多个独立证据源一致支持 | 日志明确显示数据不一致，数据库查询验证了不一致 |
| 中 | `medium` | 存在较强支持证据；但仍有关键缺口；部分替代解释未完全排除 | 日志显示异常，数据库查询支持假设，但缺少直接因果关系证据 |
| 低 | `low` | 主要依据间接线索；存在多种合理解释；关键证据缺失 | 仅有日志异常，未进行数据库验证，或验证结果不明确 |
| 未知 | `unknown` | 证据不足；证据相互冲突；关键数据源不可用 | 关键日志缺失，数据库权限拒绝，或查询超时 |

### 置信度评估规则

1. **置信度不是统计概率**
   - "高置信度"不等于"99%确定"
   - 而是表示"当前证据充分支持这一结论"

2. **必须考虑反证**
   - 如果有反证，置信度应降低
   - 如果反证无法解释，置信度应为 `low` 或 `unknown`

3. **必须考虑证据独立性**
   - 多个独立证据源的支持比单一证据更可靠
   - 如果所有证据都来自同一条日志，置信度应降低

4. **如果缺少决定性证据，使用 unknown**
   - 不得强行提升置信度
   - 明确说明缺失什么证据

### 结论措辞

| 置信度 | 结论措辞 |
|--------|----------|
| `high` | "已证实"、"确认为" |
| `medium` | "较强支持"、"很可能是" |
| `low` | "可能"、"疑似" |
| `unknown` | "未知"、"无法确认"、"证据不足" |

## 假设验证规则

### 1. 必须可证伪

- 每个假设必须有明确的验证条件
- 必须说明什么证据可以验证或否定该假设

### 2. 必须收集反证

- 不得只搜寻支持某个假设的证据
- 必须主动寻找反证
- 如果有反证，必须解释为什么仍然支持该假设

### 3. 必须考虑替代解释

- 列出所有可能的替代解释
- 评估每个替代解释的证据支持程度
- 说明为什么当前假设比替代解释更合理

### 4. 必须记录缺失证据

- 说明还需要什么证据才能确认或否定该假设
- 说明如何获取这些证据

## 证据引用规则

### 1. 每条主要结论必须引用证据

- 结论中提到的每个事实都必须有对应的 `evidence_id`
- 不得有无证据支持的结论

### 2. 区分事实和推断

- 事实：直接从证据中观察到的信息
- 推断：基于事实推测的结论
- 必须明确标识哪些是事实，哪些是推断

### 3. 不得将相关性当作因果性

- 时间相近不等于因果关系
- 必须有明确的机制解释为什么 A 导致 B

### 4. 不得将空结果当作不存在

- 查询返回 0 行不等于数据不存在
- 必须考虑查询条件、权限、延迟等因素

## 证据索引

在报告中必须包含证据索引，便于追溯：

```json
{
  "evidence_index": [
    {
      "evidence_id": "ev-log-001",
      "type": "log",
      "source": "action-2026.10.10",
      "summary": "广告报表查询失败：Unknown column 'channel'"
    },
    {
      "evidence_id": "ev-trace-001",
      "type": "log",
      "source": "trace-2026.10.10",
      "summary": "SQL 查询：SELECT COUNT(*) FROM ads_campaign_customers WHERE channel IN (...)"
    },
    {
      "evidence_id": "ev-sql-001",
      "type": "sql",
      "source": "mysql-report-db",
      "summary": "SHOW COLUMNS FROM ads_campaign_customers LIKE 'channel' 返回 0 行"
    }
  ]
}
```
