# Core AI Plugins

**不只是配置，而是一个 AI 驱动的开发体系。**

通过自动化门禁（Gates）、钩子（Hooks）和规则（Rules）系统，为 AI 代理（如 Claude）提供结构化的代码质量保障能力。

## 🎯 核心理念

```
Rules  = AI 认知层（自然语言规范）
Gates  = 机器验证层（AST/正则检查）
Hooks  = 自动执行层（工具调用触发）
Skills = AI 能力层（复杂任务编排）
Commands = 用户入口层（斜杠命令）
```

## 📦 插件列表

| 插件 | 版本 | 描述 |
|------|------|------|
| [core-ai-harness](core-ai-harness/) | 0.1.0 | AI 增强开发系统 - 自动化代码质量保障 |

### core-ai-harness

**功能特性：**
- 🔒 **自动化门禁** - 基于 AST-Grep 的 43 条 Java FP 规则检查
- 🪝 **智能钩子** - PostToolUse 自动扫描，错误阻断 + AI 自修复
- 📋 **编码规范** - FP 范式、架构约束、安全规则、代码风格
- 🛠️ **5 个技能** - 扫描、修复、代码审查、项目初始化、报告生成
- 📝 **3 个命令** - `/gates`、`/gate-check`、`/gate-install`

**支持的 Profile：**
- `default` - 通用 Java 项目（13 条 FP 规则 + 安全扫描）
- `fbr` - FBR 框架项目（+ 30 条 shape 规则 + lint/error-prone/build）

**详细文档：** [core-ai-harness/README.md](core-ai-harness/README.md)

## 🚀 快速开始

### 安装方式

#### 方式 1：本地安装（推荐开发调试）

```bash
# 在 Claude Code 中加载插件
claude --plugin-dir /path/to/core-ai-plugins/core-ai-harness

# 或通过插件安装命令
claude plugin install --from /path/to/core-ai-plugins
```

#### 方式 2：全局安装

```bash
# 安装到用户级插件目录
claude plugin install --from /path/to/core-ai-plugins --user
```

### 基本使用

```bash
# 检查当前项目的代码质量
/gates

# 扫描特定文件
/gate-check src/main/java/Service.java

# 安装门禁配置到项目
/gate-install
```

### 验证安装

```bash
# 验证插件配置
claude plugin validate /path/to/core-ai-plugins/core-ai-harness
```

## 📁 项目结构

```
core-ai-plugins/
├── core-ai-harness/           # 核心插件
│   ├── .claude-plugin/        # 插件配置
│   │   ├── plugin.json        # 插件元数据
│   │   └── marketplace.json   # 市场配置
│   ├── gates/                 # 门禁系统
│   │   ├── ast-grep/          # AST-Grep 规则（43 条）
│   │   │   ├── rules/fp/      # FP 范式规则
│   │   │   ├── rules/shape/   # 架构 shape 规则
│   │   │   └── sgconfig.yml   # 默认配置
│   │   ├── security/          # 安全扫描器
│   │   └── config.toml        # 门禁配置
│   ├── hooks/                 # 钩子系统
│   │   ├── hooks.json         # 钩子注册
│   │   ├── _lib/              # 共享库（零依赖）
│   │   ├── post_edit_gate.py  # PostToolUse 钩子
│   │   └── session_start.py   # SessionStart 钩子
│   ├── rules/                 # 规则文档
│   │   ├── fp-paradigm.md     # FP 编程范式
│   │   ├── architecture.md    # 架构约束
│   │   ├── security.md        # 安全规范
│   │   └── code-style.md      # 代码风格
│   ├── skills/                # 技能定义（5 个）
│   ├── commands/              # 斜杠命令（3 个）
│   ├── tests/                 # 单元测试（56 个）
│   └── PLAN.md                # 实施计划
├── PLAN.md                    # 总体计划
└── README.md                  # 本文件
```

## 🔧 开发指南

### 添加新规则

1. 在 `gates/ast-grep/rules/fp/` 创建 `.sg.yaml` 规则文件
2. 在 `sgconfig.yml` 中注册规则
3. 运行测试验证

### 本地测试

```bash
cd core-ai-harness
python3 -m unittest discover tests
```

### 代码审查

```bash
# 运行代码审查
/code-review
```

## 📊 当前状态

- ✅ 56 个单元测试全部通过
- ✅ 43 条 AST-Grep 规则已实现
- ✅ 完整文档和示例
- ✅ 生产就绪

## 🤝 贡献

欢迎贡献！请遵循以下流程：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

MIT License

## 📧 联系方式

murphy <maohua.zh@gmail.com>
