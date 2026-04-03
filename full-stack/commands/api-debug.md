---
name: api-debug
description: 构建HTTP请求并验证响应，检查API契约一致性
triggers:
  - /api-debug <endpoint>
parameters:
  - name: endpoint
    required: true
    description: API端点路径，如"/api/users/login"
  - name: --method
    description: HTTP方法
    default: GET
  - name: --validate
    description: 验证响应契约一致性
    default: true
---

# API Debug API调试

构建HTTP请求，分析响应，验证API契约一致性，适合API开发与联调场景。

## 执行流程

```
构建请求 → 发送请求 → 分析响应 → 契约检查 → 输出报告
```

## 使用示例

```
/api-debug /api/users/login --method=POST
/api-debug /api/orders --validate=false
```