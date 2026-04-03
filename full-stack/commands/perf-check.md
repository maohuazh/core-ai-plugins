---
name: perf-check
description: 执行性能瓶颈分析，识别热路径、N+1查询与内存风险
triggers:
  - /perf-check
  - /perf-check <路径>
parameters:
  - name: 路径
    description: 分析范围，默认当前目录
  - name: --include-sql
    description: 包含SQL性能分析
    default: true
---

# Perf Check 性能检查

识别性能瓶颈，输出可操作的优化建议，建议在上线前执行。

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