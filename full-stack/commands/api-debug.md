---
name: api-debug
description: HTTP请求构建、响应验证、契约检查
triggers:
  - /api-debug <endpoint>
parameters:
  - name: endpoint
    required: true
    description: API端点路径
  - name: --method
    description: HTTP方法
    default: GET
  - name: --validate
    description: 验证响应契约
    default: true
---

# API Debug API调试

构建HTTP请求，验证响应，检查契约一致性。

## 执行流程

```
构建请求 → 发送请求 → 分析响应 → 契约检查 → 输出报告
```

## 使用示例

```
/api-debug /api/users/login --method=POST
/api-debug /api/orders --validate=false
```