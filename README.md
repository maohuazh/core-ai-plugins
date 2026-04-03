# Core AI Plugins

专业化 Claude Code 开发工作流插件集，提供从需求分析到质量交付的全流程支持。

## 插件一览

| 插件 | 核心定位 | 命令数 | 代理数 | 适用场景 |
|------|----------|--------|--------|----------|
| **core-ng** | 新一代开发工作流 | 4 | 4 | 全复杂度覆盖、规划实现分离 |
| **holistic-dev** | 全面功能开发 | 1 | 3 | 复杂功能、深度分析 |

---

## core-ng

新一代开发工作流插件，提供规划、快速开发、实现三个命令，配备代码探索、架构设计、代码审查、测试验证四个专业代理。

### 命令

| 命令 | 阶段 | 适用场景 |
|------|------|----------|
| `/sketch-dev` | 4 | 中小型功能、需求明确 |
| `/holistic-dev` | 9 | 复杂功能、跨系统、需深度分析 |
| `/plan` | 5 | 规划阶段独立，输出PLAN.md |
| `/implement` | 6 | 基于PLAN.md执行实现 |

### 代理

| 代理 | 核心任务 |
|------|----------|
| `code-explorer` | 深度追踪代码执行路径，映射架构层次 |
| `code-architect` | 分析代码库模式，输出实现蓝图 |
| `code-reviewer` | 多维度审查，置信度过滤（仅报告≥80） |
| `code-tester` | 制定测试策略，验证覆盖率 |

### 核心特性

- **流程适配复杂度**：简单任务精简流程，复杂功能完整流程
- **规划实现可分离**：支持独立规划、审批后再实现
- **置信度驱动审查**：仅报告高置信度问题，消除噪音

**详细文档**：[core-ng/README.md](core-ng/README.md)

---

## holistic-dev

全面功能开发插件，配备专门的代理用于需求分析、Prompt优化、代码库探索、架构设计和质量审查。

### 命令

| 命令 | 阶段 | 核心流程 |
|------|------|----------|
| `/holistic-dev` | 8 | 发现→探索→澄清→架构→拆解→实现→审查→总结 |

### 代理

| 代理 | 核心任务 |
|------|----------|
| `code-explorer` | 追踪执行路径，分析架构模式 |
| `code-architect` | 设计多方案架构蓝图 |
| `code-reviewer` | 审查bug、质量、项目约定 |

### 核心特性

- **需求驱动**：从需求发现开始，确保理解完整
- **多方案设计**：最小变更、清晰架构、务实平衡三种方案
- **质量闭环**：4维度代码审查确保交付质量

**详细文档**：[holistic-dev/README.md](holistic-dev/README.md)

---

## 插件选择指南

```
任务判断
├── 简单/中型功能？
│   ├── 需求明确 → core-ng: /sketch-dev
│   └── 需求模糊 → 先澄清
├── 复杂功能？
│   ├── 需单独审批 → core-ng: /plan + /implement
│   ├── 全流程一次完成 → core-ng: /holistic-dev
│   └── 需Prompt优化 → holistic-dev: /holistic-dev
└── 已有方案？ → core-ng: /implement
```

---

## 目录结构

```
core-ai-plugins/
├── README.md                   # 仓库文档
├── .claude-plugin/
│   └ marketplace.json          # 插件市场配置
├── core-ng/                    # 新一代开发插件
│   ├── README.md
│   ├── commands/
│   │   ├── plan.md
│   │   ├── implement.md
│   │   ├── sketch-dev.md
│   │   └── holistic-dev.md
│   └ agents/
│   │   ├── code-explorer.md
│   │   ├── code-architect.md
│   │   ├── code-reviewer.md
│   │   └── code-tester.md
└── holistic-dev/               # 全面开发插件
    ├── README.md
    ├── commands/
    │   └ holistic-dev.md
    └ agents/
    │   ├── code-explorer.md
    │   ├── code-architect.md
    │   └ code-reviewer.md
```

---

## 安装使用

插件通过 Claude Code 的插件系统自动加载。在 Claude Code 中使用对应命令即可触发工作流。

**使用示例**：
```bash
# 快速开发
/sketch-dev 为API添加缓存功能

# 全面开发
/holistic-dev 实现用户认证模块

# 仅规划
/plan 设计订单处理系统

# 基于规划实现
/implement
```

---

## 设计理念

**专业分工**：每个代理专注于特定领域（探索、架构、审查、测试），输出结构化、可执行的结果。

**置信度过滤**：代码审查基于置信度评分（0-100），仅报告≥80的高优先级问题，消除噪音干扰。

**流程适配**：根据任务复杂度匹配工作流深度，避免过度分析简单任务或简化复杂功能。

---

## 作者

Murphy Zhang (maohua.zh@gmail.com)

## 版本

- core-ng: v1.0.0
- holistic-dev: v1.0.0