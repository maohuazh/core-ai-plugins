---
name: review
description: 独立代码审查，多维度质量检查
triggers:
  - /review
  - /review <路径>
parameters:
  - name: 路径
    description: 审查范围
  - name: --dimensions
    description: 检查维度 (bug,quality,security,arch)
    default: bug,quality
---

# Review 代码审查

多维度审查代码质量，置信度过滤高价值问题。

## 检查维度

| 维度 | 检查项 |
|------|--------|
| bug | 空指针、边界、并发 |
| quality | 重复、复杂度、命名 |
| security | 注入、认证、敏感数据 |
| arch | 分层、依赖、职责 |

## 使用示例

```
/review
/review src/modules/payment --dimensions=bug,security
```