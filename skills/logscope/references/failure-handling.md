# 故障处理方式

## 概述

定义日志缺失、权限拒绝、查询失败、超时和结果截断等情况的处理方式，确保在异常情况下仍能输出部分调查结果，而不是伪造完整结论。

## 核心原则

1. **容错设计**：单个数据源失败不导致伪造完整结论
2. **明确报告**：允许输出部分调查结果，但必须明确报告失败状态
3. **不伪装**：不得将未知状态伪装成确定结论
4. **可追溯**：所有失败情况都必须记录并可在报告中查看

## 故障类型与处理方式

### 1. Elasticsearch 不可用

**症状**：
- ES 集群无法连接
- 查询超时
- 返回 5xx 错误

**处理方式**：
```json
{
  "investigation_status": "failed",
  "failure_reason": "Elasticsearch 集群不可用",
  "failure_details": {
    "component": "elasticsearch",
    "error": "Connection refused",
    "timestamp": "2026-10-10T11:20:00Z"
  },
  "partial_results": null,
  "recommendation": "检查 ES 集群状态，稍后重试"
}
```

**报告输出**：
- 调查状态标记为 `failed`
- 说明失败原因和时间
- 不生成根因结论
- 建议检查 ES 集群状态

### 2. Elasticsearch 部分分片失败

**症状**：
- 查询返回结果，但包含分片失败信息
- `failed_shards` > 0

**处理方式**：
```json
{
  "investigation_status": "partial",
  "log_search_status": "partial",
  "failure_details": {
    "component": "elasticsearch",
    "error": "Partial shard failure",
    "total_shards": 10,
    "successful_shards": 8,
    "failed_shards": 2
  },
  "recommendation": "结果可能不完整，建议检查分片状态后重试"
}
```

**报告输出**：
- 调查状态标记为 `partial`
- 说明分片失败情况
- 明确说明结果可能不完整
- 降低结论置信度

### 3. correlation_id 没有结果

**症状**：
- 使用 correlation_id 查询返回 0 行
- 可能是时间窗太窄、字段 mapping 问题或索引未覆盖

**处理方式**：
```json
{
  "investigation_status": "partial",
  "correlation_search_status": "no_rows",
  "failure_details": {
    "component": "elasticsearch",
    "query": "correlation_id:A1258818EADBFBE7C5BC",
    "time_range": "2026-10-10T11:17:00Z - 2026-10-10T11:18:00Z",
    "possible_reasons": [
      "时间窗太窄",
      "字段 mapping 问题",
      "索引未覆盖该时间范围",
      "correlation_id 缺失或复用"
    ]
  },
  "recommendation": "扩大时间窗或检查字段 mapping"
}
```

**报告输出**：
- 说明查询条件和时间范围
- 列出可能的原因
- 建议扩大时间窗或检查 mapping
- 不影响其他调查步骤

### 4. ref_id 循环

**症状**：
- 追踪 ref_id 时发现循环引用
- A → B → C → A

**处理方式**：
```json
{
  "investigation_status": "completed",
  "ref_trace_status": "partial",
  "cycle_detected": true,
  "cycle_details": {
    "cycle_path": ["A", "B", "C", "A"],
    "stopped_at": "A"
  },
  "recommendation": "检查业务逻辑是否存在循环调用"
}
```

**报告输出**：
- 记录循环路径
- 说明在何处停止追踪
- 建议检查业务逻辑
- 不影响其他路径的追踪

### 5. 查询超时

**症状**：
- ES 查询超时（默认 30 秒）
- 数据库查询超时

**处理方式**：
```json
{
  "investigation_status": "partial",
  "query_status": "timeout",
  "failure_details": {
    "component": "elasticsearch",
    "query": "...",
    "timeout": "30s",
    "attempted_actions": [
      "缩小时间窗",
      "减少返回字段",
      "限制结果数量"
    ]
  },
  "recommendation": "进一步缩小查询范围或使用 scroll API"
}
```

**报告输出**：
- 说明查询超时
- 列出已尝试的优化措施
- 建议进一步缩小范围
- 不将超时等同于数据不存在

### 6. 数据库拒绝访问

**症状**：
- 数据库返回权限拒绝错误
- Access denied
- 403 Forbidden

**处理方式**：
```json
{
  "investigation_status": "partial",
  "database_query_status": "denied",
  "failure_details": {
    "component": "database",
    "datasource_id": "mysql-report-db",
    "error": "Access denied for user 'readonly'@'10.0.66.110'",
    "query": "SELECT ..."
  },
  "recommendation": "检查数据库权限配置，或尝试其他数据源"
}
```

**报告输出**：
- 说明权限拒绝
- 记录数据源和查询语句
- 不推断数据不存在
- 建议检查权限配置

### 7. 数据库结果截断

**症状**：
- 查询返回结果，但标记为截断
- `truncated: true`

**处理方式**：
```json
{
  "investigation_status": "partial",
  "database_query_status": "truncated",
  "failure_details": {
    "component": "database",
    "query_id": "Q1",
    "returned_rows": 100,
    "total_rows": 500,
    "truncation_reason": "max_rows limit (100)"
  },
  "recommendation": "结果不完整，结论置信度降低"
}
```

**报告输出**：
- 说明结果截断
- 记录返回行数和总行数
- 降低结论置信度
- 建议缩小查询范围或增加限制

### 8. 多数据源状态冲突

**症状**：
- 主库和从库返回不同的数据
- 缓存和数据库数据不一致

**处理方式**：
```json
{
  "investigation_status": "partial",
  "data_source_conflict": true,
  "conflict_details": {
    "primary_datasource": {
      "datasource_id": "mysql-report-db-primary",
      "data": { "status": "PAID" }
    },
    "replica_datasource": {
      "datasource_id": "mysql-report-db-replica",
      "data": { "status": "PENDING" }
    },
    "possible_reasons": [
      "复制延迟",
      "事务未提交",
      "缓存未失效"
    ]
  },
  "recommendation": "检查数据权威性、更新时间和一致性策略"
}
```

**报告输出**：
- 说明数据源冲突
- 记录各数据源返回的数据
- 列出可能的原因（复制延迟、事务未提交等）
- 建议检查数据权威性

### 9. 报告渲染失败

**症状**：
- HTML 模板渲染错误
- 数据格式不符合 Schema

**处理方式**：
```json
{
  "investigation_status": "completed",
  "report_generation_status": "failed",
  "failure_details": {
    "component": "report_generator",
    "error": "Template rendering failed",
    "structured_result_available": true
  },
  "recommendation": "保留结构化结果，稍后重新生成报告"
}
```

**报告输出**：
- 保留结构化结果（JSON）
- 说明报告生成失败
- 建议稍后重试

### 10. 证据引用过期

**症状**：
- 日志保留期已过
- 无法回查原始日志

**处理方式**：
```json
{
  "investigation_status": "partial",
  "evidence_availability": "partial",
  "failure_details": {
    "unavailable_evidence": ["ev-log-001"],
    "reason": "日志保留期已过（30 天）",
    "impact": "无法验证结论"
  },
  "recommendation": "在报告中标明证据过期风险"
}
```

**报告输出**：
- 说明证据不可用
- 记录过期原因
- 说明对结论的影响
- 建议尽快调查

---

## 调查状态模型

### 整体调查状态

| 状态 | 含义 | 报告输出 |
|------|------|----------|
| `completed` | 调查已结束，结论和限制已整理 | 完整报告 |
| `partial` | 调查已取得部分证据，但关键范围未完成 | 部分报告，明确说明缺失部分 |
| `blocked` | 权限或关键工具限制导致无法继续 | 说明阻塞原因和建议 |
| `failed` | 调查流程发生无法恢复的错误 | 说明失败原因和建议 |

### 阶段状态

每个调查阶段都有独立的状态：

| 状态 | 含义 |
|------|------|
| `not_started` | 未开始 |
| `running` | 进行中 |
| `completed` | 已完成 |
| `partial` | 部分完成 |
| `failed` | 失败 |
| `skipped` | 跳过（不适用或依赖的阶段失败） |
| `not_authorized` | 未授权 |

### 状态记录示例

```json
{
  "investigation_id": "INV-2026-10-10-001",
  "investigation_status": "partial",
  "phase_status": {
    "A_parse_initial_error": "completed",
    "B_correlation_search": "completed",
    "C_ref_trace": "partial",
    "D_business_key_search": "completed",
    "E_trace_detail": "completed",
    "F_hypothesis": "completed",
    "G_database_verification": "denied",
    "H_synthesis": "completed",
    "I_report_generation": "completed",
    "J_final_review": "completed"
  },
  "data_source_status": {
    "elasticsearch": "completed",
    "mysql_report_db": "denied",
    "mysql_order_db": "not_authorized"
  }
}
```

---

## 部分调查结果输出

即使调查未完成，也应输出部分结果：

### 1. 已有证据

- 列出已收集的所有证据
- 说明证据的来源和状态

### 2. 初步结论

- 基于已有证据的初步结论
- 明确说明结论的置信度（通常较低）
- 说明哪些证据还缺失

### 3. 未完成的调查步骤

- 列出未完成的调查步骤
- 说明未完成的原因
- 建议如何继续调查

### 4. 建议和限制

- 说明当前调查的限制
- 建议下一步调查方向
- 说明需要什么权限或工具

---

## 错误恢复策略

### 1. 自动重试

对于临时性错误（网络超时、服务不可用），可以自动重试：

```json
{
  "retry_policy": {
    "max_retries": 3,
    "retry_delay": "5s",
    "retry_on": ["timeout", "unavailable"]
  }
}
```

### 2. 降级策略

如果主要数据源不可用，尝试备用数据源：

```json
{
  "fallback_strategy": {
    "primary": "mysql-report-db-primary",
    "fallback": ["mysql-report-db-replica", "mysql-report-db-cache"]
  }
}
```

### 3. 手动干预

如果自动恢复失败，需要手动干预：

- 检查数据源状态
- 调整查询参数
- 申请权限
- 联系运维团队

---

## 报告中的失败信息展示

### 1. 调查状态徽章

在报告顶部展示调查状态：

```html
<div class="investigation-status">
  <span class="badge badge-warning">partial</span>
  <span>调查部分完成，部分数据源不可用</span>
</div>
```

### 2. 失败详情章节

添加专门的失败详情章节：

```html
<section id="failures">
  <h2>调查失败详情</h2>
  <table>
    <thead>
      <tr>
        <th>阶段</th>
        <th>状态</th>
        <th>错误信息</th>
        <th>影响</th>
        <th>建议</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>数据库验证</td>
        <td><span class="badge badge-error">denied</span></td>
        <td>Access denied for user 'readonly'</td>
        <td>无法验证数据假设，置信度降低</td>
        <td>检查数据库权限配置</td>
      </tr>
    </tbody>
  </table>
</section>
```

### 3. 置信度调整

如果调查过程中有失败，应降低结论置信度：

```json
{
  "primary_root_cause": {
    "category": "data_error",
    "confidence": "low",
    "confidence_reason": "数据库验证失败，无法完全确认根因"
  }
}
```

---

## 最佳实践

1. **尽早发现失败**：在每个阶段开始时检查依赖是否可用
2. **快速失败**：如果关键数据源不可用，尽早停止调查
3. **保留部分结果**：即使调查失败，也保留已收集的证据
4. **明确沟通**：在报告中清楚说明失败情况和影响
5. **提供建议**：给出下一步调查的建议和所需权限
6. **记录审计信息**：记录所有失败情况，便于后续分析
