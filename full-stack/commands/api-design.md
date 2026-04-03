---
name: api-design
description: 设计RESTful API契约，生成接口文档与类型定义
triggers:
  - /api-design <功能描述>
parameters:
  - name: 功能描述
    required: true
    description: API功能描述，如"用户登录接口"
  - name: --style
    description: API风格 (restful|graphql|rpc)
    default: restful
  - name: --output
    description: 文档输出目录
    default: docs/api
---

# API Design API设计

设计符合规范的API契约，自动生成接口文档与类型定义。

## 设计流程

```
需求分析 → 资源识别 → 路径设计 → 方法定义 → 契约输出 → 类型生成
```

## 设计规范

**RESTful约定**
- 资源命名：复数名词，小写
- 路径层级：/资源/{id}/子资源
- 方法映射：
  - GET: 查询
  - POST: 创建
  - PUT: 全量更新
  - PATCH: 部分 更新
  - DELETE: 删除

**响应规范**
- 成功：2xx状态码 + 数据
- 客户端错误：4xx状态码 + 错误信息
- 服务端错误：5xx状态码 + 错误信息

**版本管理**
- URL路径版本：/v1/resource
- Header版本：Accept: application/vnd.api+json;version=1

## 输出模板

```markdown
# API设计文档

## 接口概述
- 功能: 用户登录
- 版本: v1
- 风格: RESTful

## 端点定义

### 用户登录
**POST /v1/auth/login**

#### 请求体
```json
{
  "email": "string (required)",
  "password": "string (required)"
}
```

#### 成功响应 (200)
```json
{
  "token": "string",
  "user": {
    "id": "integer",
    "email": "string",
    "name": "string"
  }
}
```

#### 错误响应 (401)
```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "邮箱或密码错误"
  }
}
```

## 类型定义

### TypeScript
```typescript
interface LoginRequest {
  email: string;
  password: string;
}

interface LoginResponse {
  token: string;
  user: User;
}
```
```

## 使用示例

```
/api-design 用户登录接口
/api-design 订单管理模块 --style=graphql
/api-design 支付回调 --output=docs/openapi
```

## 与其他命令协作

```
/api-design → /implement → /api-debug → /test-gen
```