# Full Stack Engineer Plugin

全栈工程师插件 - 让 Claude Code 能够独立完成从项目设计到验收交付的全生命周期工作。

## 功能特性

- 🎯 **需求分析**：理解需求、澄清问题、制定技术方案
- 🏗️ **架构设计**：系统架构、技术选型、数据库设计
- 💻 **全栈开发**：前端 UI、后端 API、数据库操作
- 🔍 **代码审查**：质量检查、安全扫描、性能分析
- ✅ **测试生成**：单元测试、集成测试、覆盖率保证
- 📝 **文档编写**：项目文档、API 文档、架构说明

## 安装使用

### 方式一：本地加载（开发测试）
```bash
claude --plugin-dir ./full-stack-plugin
```

### 方式二：安装到项目
将插件目录复制到项目 `.claude/plugins/` 目录：
```bash
mkdir -p .claude/plugins
cp -r full-stack-plugin .claude/plugins/
```

### 方式三：安装到用户目录
将插件目录复制到用户级插件目录：
```bash
cp -r full-stack-plugin ~/.claude/plugins/
```

## 可用技能

| 技能 | 命令 | 功能 |
|------|------|------|
| 全栈开发 | `/full-stack-plugin:full-stack-dev [需求]` | 执行完整开发流程 |
| 项目初始化 | `/full-stack-plugin:project-init [类型] [名称]` | 快速创建项目骨架 |
| 部署 | `/full-stack-plugin:deploy [环境] [服务]` | 执行部署操作 |
| 提交 | `/full-stack-plugin:commit` | 规范化 Git 提交 |

## 可用代理

| 代理 | 调用方式 | 功能 |
|------|----------|------|
| 需求分析 | `@requirement-analyzer` 或自然语言提及 | 深度需求分析 |
| 架构师 | `@architect` | 架构设计规划 |
| 前端开发 | `@frontend-dev` | 前端专项开发 |
| 后端开发 | `@backend-dev` | 后端专项开发 |
| 代码审查 | `@code-reviewer` | 代码质量检查 |
| 测试生成 | `@test-generator` | 测试代码生成 |
| 文档编写 | `@doc-writer` | 技术文档编写 |

## 使用示例

### 1. 初始化新项目
```
/full-stack-plugin:project-init react-node my-awesome-app
```

### 2. 开发完整功能
```
/full-stack-plugin:full-stack-dev 实现用户认证系统，包括注册、登录、密码重置功能
```

### 3. 使用代理协作
```
使用 requirement-analyzer 分析用户管理模块需求
然后让 architect 设计架构方案
接着让 frontend-dev 和 backend-dev 分别实现
最后让 code-reviewer 审查代码质量
```

### 4. 部署应用
```
/full-stack-plugin:deploy staging web-service
```

## 工作流程

插件采用分层协作模式：

```
┌─────────────────────────────────────────────────────┐
│                    用户需求                          │
└─────────────────────┬───────────────────────────────┘
                      │
        ┌─────────────▼─────────────┐
        │    requirement-analyzer    │  需求分析
        └─────────────┬─────────────┘
                      │
        ┌─────────────▼─────────────┐
        │        architect          │  架构设计
        └─────────────┬─────────────┘
                      │
    ┌─────────────────┴─────────────────┐
    │                                   │
┌───▼───┐                         ┌───▼───┐
│frontend│                         │backend│  分层开发
│  -dev  │                         │  -dev │
└───┬───┘                         └───┬───┘
    │                                   │
    └─────────────────┬─────────────────┘
                      │
        ┌─────────────▼─────────────┐
        │     code-reviewer         │  代码审查
        └─────────────┬─────────────┘
                      │
        ┌─────────────▼─────────────┐
        │     test-generator        │  测试生成
        └─────────────┬─────────────┘
                      │
        ┌─────────────▼─────────────┐
        │       doc-writer          │  文档编写
        └───────────────────────────┘
```

## 技术栈支持

### 前端
- React + TypeScript + Vite
- Vue + TypeScript + Vite
- Next.js

### 后端
- Node.js + Express/NestJS
- Python + FastAPI
- Go + Gin

### 数据库
- PostgreSQL
- MongoDB
- Redis

## 配置说明

插件支持项目级记忆持久化，各代理会在以下目录保存学习内容：
- `.claude/agent-memory/` - 项目级代理记忆
- `~/.claude/agent-memory/` - 用户级代理记忆

## 许可证

MIT License