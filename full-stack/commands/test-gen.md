---
name: test-gen
description: 分析代码逻辑，自动生成测试用例（正常/边界/异常场景全覆盖）
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
    description: 目标覆盖率百分比
    default: 80
---

# Test Gen 测试生成

分析代码逻辑，智能生成覆盖完整的测试用例，提升测试效率。

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