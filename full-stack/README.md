# Full-Stack 全栈工程师插件系统

为全栈工程师设计的综合性Claude Code插件，融合架构设计、开发体验优化与质量保障三大核心维度。

---

## 设计理念

**三层体系**：战略规划（holistic-dev）+ 快速执行（sketch-dev）+ 日常工具（专项命令）

**核心原则**：
- 精准简约：每行描述深思熟虑，无冗余
- 可组合性：命令可独立执行，可编排流水线
- 置信度过滤：仅报告≥80置信度的高价值问题
- 渐进复杂度：快捷模式→引导模式→专家模式

---

## 核心Agents (12个)

| Agent | 职责 | 触发场景 |
|-------|------|----------|
| `code-explorer` | STRIDE探索法追踪执行路径，映射架构层次与依赖关系 | 理解现有代码、定位修改点 |
| `code-architect` | 分析代码库模式，方案评估维度表，输出实现蓝图与构建序列 | 设计架构方案、多方案比较 |
| `code-reviewer` | 多维度审查（Bug/Security/Quality/Performance/Maintainability），置信度过滤 | 代码变更后质量保障 |
| `code-tester` | 制定测试策略，覆盖率标准表，测试盲区识别 | 功能实现后验证策略 |
| `context-synthesizer` | 三阶段整合流程，聚合多代理输出，优先级排序 | 多代理并行后整合 |
| `test-generator` | 自动生成测试用例（正常/边界/异常/集成），框架适配 | 新功能完成、覆盖率不足 |
| `security-scanner` | 输入验证/认证授权/敏感数据/依赖漏洞四维度扫描 | 定期扫描、安全审计 |
| `performance-analyzer` | 热路径/N+1查询/内存泄漏/慢查询检测，优先级评估矩阵 | 性能优化、上线前检查 |
| `architect-guard` | 分层违规/循环依赖/接口污染/职责越界检测，严重度评估 | 架构一致性守护 |
| `crud-generator` | Model→Repository→Service→API→Test全栈代码生成 | 标准业务模块快速搭建 |
| `doc-generator` | API文档/README/CHANGELOG/架构文档自动生成 | 文档同步、项目说明 |
| `refactor-assistant` | 代码异味检测，重构机会识别，安全等级判定 | 代码重构场景 |

---

## 核心Commands

### 开发流程类

| Command | 功能 | 参数 | 使用场景 |
|---------|------|------|----------|
| `/sketch-dev` | 快速交付中小型功能，4阶段精简流程（探索→规划→实现→审查） | `<功能描述> [--skip-review] [--include-test]` | 需求明确、改动可控的中小型功能 |
| `/holistic-dev` | 深度交付复杂功能，9阶段全流程（需求澄清→探索→分析→规划→评审→实现→测试→审查→整合） | `<功能描述> [--skip-clarify] [--include-test] [--depth]` | 跨模块复杂功能、涉及架构调整 |
| `/plan` | 深度分析并输出实现蓝图，等待审批后再执行实现 | `<功能描述> [--output=PLAN.md] [--depth]` | 需预先审批的实现方案 |
| `/implement` | 读取已审批的实现蓝图，按序列执行代码实现 | `[--plan=PLAN.md] [--from-step=N]` | 已有蓝图执行实现，支持断点续传 |
| `/explore` | 深度探索代码库，输出架构层次、执行路径与必读文件清单 | `<功能/模块> [--depth=deep]` | 快速理解现有代码结构 |
| `/refactor` | 分析重构范围与影响链路，生成安全的重构执行计划 | `<目标> [--scope=file,module,system]` | 代码重构场景，含变更预览与回滚点 |

### 质量保障类

| Command | 功能 | 使用时机 |
|---------|------|----------|
| `/review` | 执行多维度代码审查，置信度过滤确保输出高价值问题 | 变更后质量检查（置信度≥80） |
| `/test-gen` | 分析代码逻辑，自动生成测试用例（正常/边界/异常场景全覆盖） | 新功能完成、覆盖率不足 |
| `/qa-gate` | 执行全量质量门禁检查（测试→覆盖率→安全→性能→架构） | PR提交前、发布前 |
| `/security-scan` | 执行安全漏洞扫描，检测代码缺陷与敏感信息泄露风险 | 定期扫描、安全审计 |
| `/perf-check` | 执行性能瓶颈分析，识别热路径、N+1查询与内存风险 | 性能优化、上线前检查 |
| `/tech-debt` | 盘点技术债务，识别代码异味、过时依赖与重构优先级 | 迭代规划、重构评估 |
| `/pr-ready` | 执行PR就绪检查，验证代码符合合并标准并生成PR模板 | 创建PR前 |

### 日常工具类

| Command | 功能 | 适用场景 |
|---------|------|----------|
| `/db-migrate` | 生成数据库迁移脚本（含回滚），支持版本追踪与依赖分析 | Schema变更、数据迁移 |
| `/api-debug` | 构建HTTP请求并验证响应，检查API契约一致性 | API开发、联调测试 |

### 需求与设计类

| Command | 功能 | 使用场景 |
|---------|------|----------|
| `/requirement-analyze` | 分析需求描述，识别功能边界、验收标准与技术风险 | 需求澄清、迭代规划 |
| `/api-design` | 设计RESTful API契约，生成接口文档与类型定义 | API设计阶段 |

### 部署与维护类

| Command | 功能 | 使用时机 |
|---------|------|----------|
| `/deploy-prep` | 执行部署前检查，验证配置、环境与依赖就绪状态 | 发布前准备 |
| `/dep-check` | 检查依赖更新、安全漏洞与许可证风险 | 定期维护、安全审计 |

---

## 质量门禁流水线

```
/qa-gate 执行流程:
Stage 1: 测试执行 → 覆盖率收集
Stage 2: 覆盖率分析 → 门禁判断（核心90%/重要80%/一般60%）
Stage 3: 安全扫描 → SAST + 依赖漏洞 + 敏感信息
Stage 4: 性能分析 → 热路径 + N+1查询 + 内存风险
Stage 5: 架构守护 → 分层检查 + 依赖方向 + 接口边界

输出: 质量报告.md
├─ 通过项 ✅
├─ 告警项 ⚠️ （可选修复）
└─ 阻塞项 ❌ （必须修复）
```

---

## 交互优化设计

**错误处理分级**
| 级别 | 示例 | 处理策略 |
|------|------|----------|
| 致命 | 编译失败、运行时崩溃 | 立即阻断，提供修复代码 |
| 警告 | 代码异味、潜在风险 | 记录不阻断，阶段后汇总 |
| 提示 | 优化机会、最佳实践 | 可选采纳，不干扰主流程 |

**认知负载优化**
- 决策点最小化：每阶段最多3个关键问题
- 信息分层：摘要先行，详情按需展开
- 上下文感知：基于文件类型、项目栈智能推荐

**安全网设计**
- 操作预览：文件变更前展示diff
- 回退点：关键阶段前创建Git stash
- 影响评估：变更前分析依赖关系

---

## 工作流组合

```
完整开发链:
/requirement-analyze → /plan → 用户审批 → /implement → /test-gen → /review → /qa-gate → /deploy-prep

快捷模式:
/sketch-dev --include-test

PR准备:
/pr-ready → (自动执行) /test-gen + /security-scan + /review

日常迭代:
/explore → /implement → /review

设计先行:
/api-design → /implement → /api-debug

依赖维护:
/tech-debt → /dep-check → /refactor
```

---

## 测试金字塔支持

```
      /\
     /E2E\      5% - 关键流程验证
    /------\
   / 集成测试 \   15% - 组件交互、API契约
  /----------\
 /   单元测试  \  80% - 逻辑正确性、边界条件
/--------------\
```

---

## 置信度分级

| 分数 | 判定 | 处理策略 |
|------|------|----------|
| 0-79 | 低置信度 | 过滤不报告 |
| 80-89 | 确定问题 | 必须处理 |
| 90-99 | 严重问题 | 优先修复 |
| 100 | 致命问题 | 立即阻塞 |

---

## Git Hooks 配置

| Hook | 触发时机 | 执行命令 | 超时 |
|------|----------|----------|------|
| pre-commit | 提交前 | security-scan, review | 120s |
| pre-push | 推送前 | qa-gate | 300s |
| pre-pr | PR创建前 | qa-gate, pr-ready | 300s |
| post-merge | 合并后 | tech-debt (异步) | - |

---

## 工作流预设

| 预设 | 命令序列 | 适用场景 |
|------|----------|----------|
| standard | plan → implement → test-gen → review → qa-gate → pr-ready | 标准开发流程 |
| quick | sketch-dev → pr-ready | 快速迭代 |
| comprehensive | holistic-dev → qa-gate → deploy-prep | 复杂功能交付 |
| hotfix | explore → implement → security-scan → pr-ready | 紧急修复 |

---

## 插件协作关系

```
core-ng / holistic-dev          full-stack (本插件)
         │                              │
         ▼                              ▼
    开发阶段                        质量阶段
         │                              │
         ├─ code-explorer ─────────────┼─► architect-guard
         │                              │
         ├─ code-architect ─────────────┼─► security-scanner
         │                              │
         ├─ code-tester ────────────────┼─► test-generator
         │                              │
         └─ code-reviewer ◄────────────┴─► 所有质量Agent
```

---

## 目录结构

```
full-stack/
├── .claude-plugin/
│   ├── plugin.json       # 主配置（含commands/agents/hooks/dependencies）
│   └── hooks.json        # Git钩子配置
├── README.md
├── commands/             # 19个命令
│   ├── sketch-dev.md
│   ├── holistic-dev.md
│   ├── plan.md
│   ├── implement.md
│   ├── review.md
│   ├── explore.md
│   ├── test-gen.md
│   ├── refactor.md
│   ├── qa-gate.md
│   ├── security-scan.md
│   ├── perf-check.md
│   ├── tech-debt.md
│   ├── pr-ready.md
│   ├── db-migrate.md
│   ├── api-debug.md
│   ├── requirement-analyze.md
│   ├── deploy-prep.md
│   ├── api-design.md
│   └── dep-check.md
└── agents/               # 12个代理
    ├── code-explorer.md
    ├── code-architect.md
    ├── code-reviewer.md
    ├── code-tester.md
    ├── context-synthesizer.md
    ├── test-generator.md
    ├── security-scanner.md
    ├── performance-analyzer.md
    ├── architect-guard.md
    ├── crud-generator.md
    ├── doc-generator.md
    └── refactor-assistant.md
```