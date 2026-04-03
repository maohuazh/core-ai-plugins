---
name: review
description: 执行多维度代码审查，置信度过滤确保输出高价值问题
triggers:
  - /review
  - /review <路径>
parameters:
  - name: 路径
    description: 审查范围，默认当前目录
  - name: --dimensions
    description: 检查维度，逗号分隔 (bug,quality,security,arch)
    default: bug,quality
---

# Review 代码审查

多维度审查代码质量，置信度过滤确保仅输出高价值问题（置信度≥80）。

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