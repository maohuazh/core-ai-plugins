---
name: implement
description: 基于规划蓝图执行实现
triggers:
  - /implement
parameters:
  - name: --plan
    description: 规划文件路径
    default: PLAN.md
  - name: --from-step
    description: 从指定步骤开始
---

# Implement 实现阶段

基于已审批的规划蓝图执行代码实现。

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