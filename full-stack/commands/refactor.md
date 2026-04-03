---
name: refactor
description: 重构辅助，识别重构范围与影响
triggers:
  - /refactor <目标>
parameters:
  - name: 目标
    required: true
    description: 重构目标描述
  - name: --scope
    description: 重构范围 (file|module|system)
    default: module
---

# Refactor 重构辅助

识别重构范围，分析影响，生成重构计划。

## 执行流程

```
识别目标 → 分析影响 → 规划步骤 → 生成计划 → 等待确认
```

## 使用示例

```
/refactor 简化用户服务类
/refactor 拆分订单处理模块 --scope=module
```