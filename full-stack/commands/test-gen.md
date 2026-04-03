---
name: test-gen
description: 分析变更代码，自动生成测试用例
triggers:
  - /test-gen
  - /test-gen <路径>
parameters:
  - name: 路径
    description: 目标代码路径
  - name: --type
    description: 测试类型 (unit|integration|all)
    default: unit
  - name: --coverage-target
    description: 目标覆盖率
    default: 80
---

# Test Gen 测试生成

分析代码逻辑，生成覆盖完整的测试用例。

## 执行流程

```
代码分析 → 边界识别 → 场景枚举 → 用例生成 → 覆盖率预估
```

## 使用示例

```
/test-gen src/modules/payment
/test-gen --type=integration
/test-gen --coverage-target=90
```