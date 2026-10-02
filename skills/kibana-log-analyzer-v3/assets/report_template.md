# Kibana 错误日志分析报告

**分析时间**: {{timestamp}}
**时间范围**: {{time_range}}
**总错误数**: {{total_errors}}
**涉及服务**: {{app_count}} 个
**错误分组**: {{group_count}} 个

---

## 一、全局统计

| 服务 (app) | 操作 (action) | 错误码 (error_code) | 错误数 | 影响等级 |
|------------|---------------|---------------------|--------|----------|
{{#each groups}}
| {{app}} | {{action}} | {{error_code}} | {{count}} | {{severity}} |
{{/each}}

## 二、详细分析

{{#each group_reports}}
### {{severity_rank}} [{{severity}}] {{app}}/{{action}}/{{error_code}}

> 错误数量: {{count}} | 最新发生: {{latest_timestamp}} | 样本日志 ID: {{sample_id}}

#### 错误概述

{{error_summary}}

#### 调用链分析

{{trace_analysis}}

#### 源码定位与根因分析

{{root_cause_analysis}}

**直接原因**: {{direct_cause}}

**根本原因**: {{root_cause}}

#### 影响范围评估

- **影响用户/请求数**: {{affected_count}}
- **影响等级**: {{severity}}
- **影响服务**: {{affected_services}}

#### 修复建议

**短期修复**（{{short_term_timeline}}）:
{{short_term_fixes}}

**长期优化**（{{long_term_timeline}}）:
{{long_term_optimizations}}

---

{{/each}}

## 三、总结与建议

### 关键发现

{{key_findings}}

### 优先级排序

{{priority_order}}

### 后续行动

{{action_items}}
