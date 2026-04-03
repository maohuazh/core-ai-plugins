---
name: plan
description: 独立规划阶段，输出实现蓝图供审批
triggers:
  - /plan <功能描述>
parameters:
  - name: 功能描述
    required: true
  - name: --output
    description: 输出文件路径
    default: PLAN.md
  - name: --depth
    description: 探索深度
    default: medium
---

# Plan 规划阶段

深度分析后输出实现蓝图，等待用户审批后再实现。

## 执行流程

```
Explore → Analyze → Design → Plan → Output → 等待审批
```

## 使用示例

```
/plan 实现用户登录日志记录
/plan 重构支付模块 --depth=deep
```