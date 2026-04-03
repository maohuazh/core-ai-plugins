---
name: deploy-prep
description: 执行部署前检查，验证配置、环境与依赖就绪状态
triggers:
  - /deploy-prep
  - /deploy-prep <环境>
parameters:
  - name: 环境
    description: 目标环境 (dev|staging|production)
    default: staging
  - name: --checklist
    description: 自定义检查清单路径
  - name: --skip-secrets
    description: 跳过敏感配置检查
---

# Deploy Prep 部署准备

执行部署前完整检查，确保环境配置、依赖与 Secrets 就绪。

## 检查维度

**环境配置**
- 环境变量完整性
- 配置文件一致性
- 特性开关状态

**依赖验证**
- 包版本一致性
- 数据库连接验证
- 外部服务可达性

**Secrets检查**
- 必需Secrets存在性
- Secrets有效期
- 权限配置正确性

**资源验证**
- 存储空间充足
- 网络配置正确
- 容器资源配置

## 输出模板

```markdown
# 部署准备报告

## 目标环境
- 环境: staging
- 部署类型: 容器部署

## 检查结果

### 通过项 ✅
- [config] 环境变量配置完整
- [deps] 数据库连接正常
- [secrets] API密钥有效期>30天

### 告警项 ⚠️
- [deps] Redis连接池配置建议优化
  当前: max_connections=10
  建议: max_connections=50

### 阻塞项 ❌
- [secrets] JWT_SECRET 未配置
  解决方案: 在Secrets管理器中添加JWT_SECRET

## 就绪状态
❌ 未就绪 - 存在1个阻塞项需解决
```

## 使用示例

```
/deploy-prep
/deploy-prep production
/deploy-prep staging --checklist=custom-checklist.md
```

## 与其他命令协作

```
/qa-gate → /deploy-prep → 部署执行
```