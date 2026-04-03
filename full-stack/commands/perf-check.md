---
name: perf-check
description: 性能分析，识别瓶颈与优化机会
triggers:
  - /perf-check
  - /perf-check <路径>
parameters:
  - name: 路径
    description: 分析范围
  - name: --include-sql
    description: 包含SQL性能分析
    default: true
---

# Perf Check 性能检查

识别性能瓶颈，输出优化建议。

## 检查项

- 热路径识别
- N+1查询检测
- 内存泄漏风险
- 慢查询分析

## 使用示例

```
/perf-check
/perf-check src/api --include-sql=true
```