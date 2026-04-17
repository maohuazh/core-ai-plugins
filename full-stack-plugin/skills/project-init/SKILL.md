---
name: project-init
description: 项目初始化技能。当用户需要快速搭建新项目、配置开发环境、创建项目骨架时激活。
disable-model-invocation: false
user-invocable: true
argument-hint: [项目类型] [项目名称]
---

# 项目初始化技能

根据 `$ARGUMENTS` 指定的项目类型和名称，快速创建项目骨架。

## 支持的项目类型

| 类型 | 前端 | 后端 | 数据库 | 适用场景 |
|------|------|------|--------|----------|
| `react-node` | React + Vite | Express + TypeScript | PostgreSQL | 快速原型开发 |
| `vue-node` | Vue + Vite | Express + TypeScript | PostgreSQL | 企业级应用 |
| `react-nest` | React + Vite | NestJS | PostgreSQL | 大型企业应用 |
| `vue-python` | Vue + Vite | FastAPI | PostgreSQL/MongoDB | 数据驱动应用 |
| `full-next` | Next.js | 内置 API | PostgreSQL | SEO友好应用 |
| `go-api` | - | Go + Gin | PostgreSQL | 高性能服务 |

## 初始化流程

### 1. 项目结构创建
根据项目类型创建标准目录结构：

```
project-name/
├── frontend/           # 前端代码
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
├── backend/            # 后端代码
│   ├── src/
│   ├── tests/
│   ├── package.json / requirements.txt
│   └── tsconfig.json / pyproject.toml
├── database/           # 数据库相关
│   ├── migrations/
│   ├── schemas/
│   └── seeds/
├── docs/               # 文档
│   ├── README.md
│   ├── API.md
│   └── ARCHITECTURE.md
├── scripts/            # 工具脚本
├── .env.example        # 环境变量示例
├── docker-compose.yml  # Docker 配置
└── README.md           # 项目主文档
```

### 2. 配置文件生成
- TypeScript/Python 配置
- ESLint/Prettier/Ruff 配置
- 测试框架配置
- Git hooks (husky)

### 3. 基础代码模板
- 用户认证模块模板
- API 路由模板
- 数据库连接模板
- 前端页面模板

### 4. 文档初始化
- README.md 快速开始指南
- API 文档框架
- 架构说明框架

## 执行步骤

1. 解析 `$ARGUMENTS` 获取项目类型和名称
2. 创建项目根目录
3. 根据类型创建目录结构
4. 生成配置文件
5. 生成基础代码模板
6. 生成文档框架
7. 初始化 Git 仓库
8. 输出下一步操作指南

## 示例

用户输入：`/project-init react-node my-app`

执行：
- 创建 React + Express + PostgreSQL 项目
- 配置 TypeScript 环境
- 配置 ESLint + Prettier
- 创建用户认证模板
- 生成 README.md