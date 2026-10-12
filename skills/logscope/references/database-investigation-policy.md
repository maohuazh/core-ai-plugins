# 数据库调查策略

## 概述

定义数据库查询的权限、只读要求、数据源选择和结果解释规则。数据库调查是验证数据层假设的重要手段，但必须严格遵守只读原则和安全约束。

## 核心原则

### 1. 只读原则

- **禁止**执行任何写操作（INSERT、UPDATE、DELETE、DDL）
- 仅执行 SELECT 查询（SQL）或 aggregate 查询（MongoDB）
- 服务端必须实施只读校验，不能仅依赖模型自律

### 2. 最小权限原则

- 仅查询验证假设所需的最小数据集
- 仅选择必要的字段，避免读取无关敏感信息
- 不得扩大查询权限或访问未授权的数据源

### 3. 授权原则

- 所有查询必须通过已授权的只读查询工具执行
- 不得绕过权限限制
- 不得将 `primary_datasource_id` 误认为已获得所有数据源的访问权限

## 何时进行数据库调查

### 适合调查的情况

1. **日志显示数据异常**
   - 记录不存在、字段为空或数据解析失败
   - 多个服务对同一业务对象的状态判断不一致
   - 唯一键冲突、重复处理或关联对象缺失

2. **异常可能与数据状态有关**
   - 软删除、租户过滤或状态字段
   - 业务流程在读取数据、关联数据或状态校验阶段失败
   - 日志和业务规则提示可能存在数据完整性问题

3. **需要验证数据假设**
   - 假设某条记录不存在
   - 假设某个字段值异常
   - 假设关联关系不一致

### 不适合调查的情况

1. **日志未指向特定业务实体**
   - 仅有异常堆栈，没有业务键
   - 无法确定需要查询哪个表或集合

2. **仅凭猜测进行调查**
   - 没有日志证据支持数据问题假设
   - 试图通过查询"发现"问题

3. **未明确权限边界**
   - 不知道有哪些数据源可用
   - 不清楚当前用户的查询权限

## 数据源语义

### primary_datasource_id vs datasource_id

| 字段 | 含义 | 用途 |
|------|------|------|
| `primary_datasource_id` | 调查主数据源 | 明确调查范围和优先级 |
| `datasource_id` | 当前查询实际执行的数据源 | 记录实际查询的数据源 |

**重要**：
- `primary_datasource_id` 是调查上下文，**不代表**自动获得其他数据源权限
- 每次查询必须明确指定 `datasource_id`
- 必须检查当前调用者对实际数据源的授权

### 数据源角色

| 角色 | 说明 | 注意事项 |
|------|------|----------|
| `primary` | 主库 | 数据最新，但可能有写入压力 |
| `replica` | 从库/副本 | 可能有复制延迟 |
| `cache` | 缓存 | 数据可能过期 |

## 数据库调查步骤

### 步骤 1：从日志提取业务键

从 action 和 trace 日志中提取：
- 业务键（如 `merchant_id`、`order_id`）
- 实体类型（如 `ads_campaign_customers` 表）
- 时间范围
- SQL 查询语句（如果有）

示例：
```json
{
  "business_keys": {
    "merchant_id": "d5673e51-9e7b-4e64-957d-767b67df8db7"
  },
  "entity_type": "ads_campaign_customers",
  "time_range": {
    "start": "2026-07-09",
    "end": "2026-10-09"
  },
  "sql_from_log": "SELECT COUNT(*) FROM ads_campaign_customers WHERE merchant_id = ? AND channel IN (?, ?)"
}
```

### 步骤 2：确定数据源

1. 明确 `primary_datasource_id`（调查主数据源）
2. 根据假设选择当前查询的 `datasource_id`
3. 检查当前调用者对实际数据源的授权

示例：
```json
{
  "primary_datasource_id": "mysql-report-db",
  "datasource_id": "mysql-report-db-replica",
  "datasource_role": "replica",
  "authorization_status": "granted"
}
```

### 步骤 3：设计查询

设计只读查询，仅选择必要字段：

**SQL 示例**：
```sql
-- 检查表结构
SHOW COLUMNS FROM ads_campaign_customers LIKE 'channel';

-- 查询业务数据
SELECT id, merchant_id, status, created_at 
FROM ads_campaign_customers 
WHERE merchant_id = 'd5673e51-...' 
  AND created_at >= '2026-07-09' 
  AND created_at <= '2026-10-09'
LIMIT 100;
```

**MongoDB 示例**：
```javascript
// 检查集合结构
db.ads_campaign_customers.findOne({ merchant_id: "d5673e51-..." });

// 查询业务数据
db.ads_campaign_customers.find(
  { 
    merchant_id: "d5673e51-...",
    created_at: { $gte: ISODate("2026-07-09"), $lte: ISODate("2026-10-09") }
  },
  { _id: 1, merchant_id: 1, status: 1, created_at: 1 }
).limit(100);
```

### 步骤 4：执行查询

记录查询执行信息：

```json
{
  "query_id": "Q1",
  "datasource_id": "mysql-report-db-replica",
  "purpose": "检查 channel 列是否存在",
  "hypothesis_id": "H-DATA-001",
  "query_type": "sql",
  "query_intent": "SHOW COLUMNS FROM ads_campaign_customers LIKE 'channel'",
  "required_fields": ["Field", "Type"],
  "safety_notes": ["只读查询", "仅查询表结构"]
}
```

### 步骤 5：检查结果

检查查询状态和结果：

```json
{
  "query_id": "Q1",
  "status": "no_rows",
  "row_count": 0,
  "truncated": false,
  "warnings": [],
  "execution_time_ms": 15,
  "evidence_id": "ev-sql-001",
  "interpretation": "channel 列在 ads_campaign_customers 表中不存在"
}
```

### 步骤 6：交叉验证

将数据库结果与日志时间线及业务规则交叉验证：

1. 日志显示 SQL 查询引用了 `channel` 列
2. 数据库查询确认 `channel` 列不存在
3. 结论：SQL 查询引用了不存在的列，导致语法错误

### 步骤 7：记录证据

将查询结果标记为证据：

```json
{
  "evidence_id": "ev-sql-001",
  "evidence_type": "sql",
  "source": "mysql-report-db-replica",
  "document_id": "Q1",
  "observed_at": "2026-10-10T11:25:00Z",
  "queried_at": "2026-10-10T11:25:00Z",
  "query_summary": "SHOW COLUMNS FROM ads_campaign_customers LIKE 'channel'",
  "result_summary": "返回 0 行，channel 列不存在",
  "row_count": 0,
  "truncated": false,
  "status": "no_rows",
  "datasource_id": "mysql-report-db-replica",
  "datasource_role": "replica",
  "hypothesis_ids": ["H-DATA-001"]
}
```

## 查询状态处理

### 状态定义

| 状态 | 含义 | 后续动作 |
|------|------|----------|
| `completed` | 查询成功完成，有结果 | 分析结果，验证假设 |
| `no_rows` | 查询成功完成，无结果 | **不等于**数据不存在，需检查查询条件 |
| `denied` | 权限拒绝 | 记录权限限制，尝试其他数据源或调整查询 |
| `timeout` | 查询超时 | 缩小查询范围，优化查询条件 |
| `unavailable` | 数据源不可用 | 尝试其他数据源，或标记为证据不足 |
| `truncated` | 结果截断 | 说明结果不完整，降低置信度 |

### 常见误判

| 观察结果 | 不应直接得出的结论 | 推荐的下一步 |
|----------|-------------------|--------------|
| SQL 返回零行 | 数据库中不存在该业务记录 | 检查查询条件、租户、软删除、事务时点和数据源 |
| MongoDB 聚合无结果 | 业务对象不存在 | 检查匹配条件、集合选择、关联阶段和权限 |
| 查询超时 | 数据库一定发生故障 | 检查执行状态、查询复杂度和其他证据 |
| 数据源拒绝访问 | 数据不存在 | 记录权限限制，并在授权范围内继续调查 |
| 两个数据源返回不同状态 | 其中一个数据源一定错误 | 检查数据权威性、更新时间、复制延迟和一致性策略 |
| 日志中字段为空 | 数据库记录一定脏 | 检查字段是否被转换、过滤、覆盖或在其他步骤丢失 |
| 同一业务键存在多条记录 | 一定是重复数据错误 | 核实业务键唯一性约束和业务模型 |

## 数据完整性检查

### 检查项

1. **记录存在性**
   - 检查业务键对应的记录是否存在
   - 考虑软删除、租户过滤

2. **关键字段为空/缺失**
   - 检查必填字段是否为 NULL 或空字符串
   - 考虑字段默认值和业务规则

3. **状态组合**
   - 检查状态字段是否符合业务规则
   - 例如：订单状态为 PENDING，但支付状态为 PAID

4. **关联记录完整性**
   - 检查外键关联的记录是否存在
   - 例如：订单引用的商品是否存在

5. **重复业务键**
   - 检查业务键是否唯一
   - 例如：同一订单号是否有多条记录

6. **时间顺序**
   - 检查时间字段是否符合逻辑顺序
   - 例如：创建时间是否晚于更新时间

7. **数量/金额一致性**
   - 检查数量和金额是否一致
   - 例如：订单总金额是否等于商品单价 × 数量

### 业务规则来源

业务规则必须有来源：
- 需求文档
- 代码规则登记
- 数据库约束（UNIQUE、NOT NULL、CHECK）
- 领域负责人确认

**重要**：对每个失败规则，输出观测值、期望条件、规则版本和证据 ID。规则失败只能表示"观察到违反规则"，不能自动推断是污染、人工修改或某次部署导致。

## 特殊场景处理

### 1. 复制延迟

**场景**：主库已写入，但从库尚未同步

**处理**：
- 记录数据源角色（primary / replica）
- 检查数据新鲜度
- 如果从库查询无结果，尝试查询主库
- 在报告中说明复制延迟情况

### 2. 事务未提交

**场景**：事务已执行但尚未提交

**处理**：
- 使用 READ COMMITTED 或更高的隔离级别
- 如果查询无结果，可能是事务未提交
- 在报告中说明事务状态

### 3. 软删除

**场景**：记录已被软删除（is_deleted = true）

**处理**：
- 查询时包含软删除的记录
- 检查删除时间和删除原因
- 在报告中说明软删除情况

### 4. 租户隔离

**场景**：多租户系统中，不同租户的数据隔离

**处理**：
- 查询时加上租户过滤条件
- 检查租户 ID 是否正确
- 在报告中说明租户隔离情况

### 5. 时区差异

**场景**：数据库使用 UTC，业务使用本地时区

**处理**：
- 统一时区（建议使用 UTC）
- 在报告中说明时区转换
- 检查时间范围是否正确

## 安全注意事项

1. **SQL 注入防护**
   - 使用参数化查询
   - 不得拼接用户输入到 SQL 语句中

2. **敏感数据脱敏**
   - 不在报告中输出密码、令牌等敏感字段
   - 对个人身份信息（PII）进行脱敏

3. **查询审计**
   - 记录所有查询的执行信息
   - 审计数据本身也应做访问控制

4. **结果大小限制**
   - 限制查询返回的行数（默认 100 行）
   - 防止查询返回过多数据

## 查询限制配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_rows` | 100 | 单次查询最大返回行数 |
| `query_timeout` | 30s | 查询超时时间 |
| `max_query_length` | 10000 | 查询语句最大长度 |
| `max_join_tables` | 5 | 最大 JOIN 表数量 |
