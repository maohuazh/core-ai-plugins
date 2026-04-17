---
name: deploy
description: 部署技能。当用户需要部署应用、配置生产环境、发布服务时激活。
disable-model-invocation: true
user-invocable: true
argument-hint: [环境] [服务]
allowed-tools: Bash(docker *, kubectl *, npm run build, pnpm build, git push, ssh *, scp *)
---

# 部署技能

执行 `$ARGUMENTS` 指定的环境和服务部署操作。

## 支持的部署环境

| 环境 | 描述 | 适用场景 |
|------|------|----------|
| `dev` | 开发环境 | 本地开发测试 |
| `staging` | 预发布环境 | 功能验证测试 |
| `prod` | 生产环境 | 正式上线服务 |

## 部署流程

### 1. 部署前检查
- 运行所有测试确保通过
- 检查代码审查状态
- 验证环境配置完整性
- 检查数据库迁移状态

### 2. 构建应用
```bash
# 前端构建
npm run build

# 后端构建
npm run build

# Docker 构建
docker build -t app-name:version .
```

### 3. 部署执行
根据环境类型执行：
- Docker 容器部署
- Kubernetes 部署
- 传统服务器部署

### 4. 部署后验证
- 服务健康检查
- API 可用性验证
- 前端页面访问验证
- 数据库连接验证

## Docker 部署模板

```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - API_URL=http://backend:3001

  backend:
    build: ./backend
    ports:
      - "3001:3001"
    environment:
      - DATABASE_URL=postgres://user:pass@db:5432/db
    depends_on:
      - db

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=db

volumes:
  postgres_data:
```

## 部署检查清单

### 部署前
- [ ] 所有测试通过
- [ ] 代码审查完成
- [ ] 环境变量配置正确
- [ ] 数据库迁移准备完成
- [ ] 版本号已更新

### 部署中
- [ ] 构建无错误
- [ ] 容器/服务启动成功
- [ ] 网络配置正确
- [ ] 数据库连接正常

### 部署后
- [ ] 服务健康检查通过
- [ ] API 响应正常
- [ ] 前端页面可访问
- [ ] 日志无异常
- [ ] 监控告警配置完成

## 回滚方案

部署失败时执行回滚：
```bash
# Docker 回滚
docker-compose down
docker-compose up -d --force-recreate previous-version

# Kubernetes 回滚
kubectl rollout undo deployment/app-name
```

## 安全注意事项

- 生产环境敏感信息使用 Secrets
- 不在代码中存储密码密钥
- 确保 HTTPS 配置
- 配置防火墙规则