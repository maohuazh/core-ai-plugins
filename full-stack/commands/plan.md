---
name: plan
description: 深度分析并输出实现蓝图，等待审批后再执行实现
triggers:
  - /plan <功能描述>
parameters:
  - name: 功能描述
    required: true
    description: 功能详述，如"实现用户登录日志记录"
  - name: --output
    description: 蓝图输出路径
    default: PLAN.md
  - name: --depth
    description: 代码探索深度 (shallow|medium|deep)
    default: medium
---

# Plan 规划阶段

深度分析后输出实现蓝图，等待用户审批后再执行实现，适合需要预先审批的场景。

## 执行流程

```
Explore → Analyze → Design → Plan → Output → 等待审批
```

## 使用示例

```
/plan 实现用户登录日志记录
/plan 重构支付模块 --depth=deep
```