---
name: implement
description: 读取已审批的实现蓝图，按序列执行代码实现
triggers:
  - /implement
parameters:
  - name: --plan
    description: 实现蓝图路径
    default: PLAN.md
  - name: --from-step
    description: 从指定步骤开始执行
---

# Implement 实现阶段

基于已审批的实现蓝图执行代码实现，支持断点续传。

## 执行流程

```
读取规划 → 按序列实现 → 验证实现 → 输出变更
```

## 使用示例

```
/implement
/implement --plan=docs/PAYMENT_PLAN.md
/implement --from-step=3
```