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

## 核心Agents

| Agent | 职责 | 触发场景 |
|-------|------|----------|
| `code-explorer` | 追踪执行路径，映射架构层次，输出必读文件清单 | 理解现有代码、定位修改点 |
| `code-architect` | 分析代码库模式，输出实现蓝图与构建序列 | 设计架构方案、多方案比较 |
| `code-reviewer` | 多维度审查，置信度过滤，输出结构化问题清单 | 代码变更后质量保障 |
| `code-tester` | 制定测试策略，生成用例清单，覆盖率分析 | 功能实现后验证 |
| `context-synthesizer` | 聚合多代理输出，消除冗余，生成统一上下文 | 多代理并行后整合 |
| `test-generator` | 基于代码分析自动生成测试用例，覆盖边界/异常/正常 | 新功能完成、覆盖率不足 |
| `security-scanner` | 输入验证、注入风险、认证授权、依赖漏洞扫描 | 定期扫描、安全审计 |
| `performance-analyzer` | 时间复杂度、N+1查询、内存泄漏、热路径识别 | 性能优化、上线前检查 |
| `architect-guard` | 分层违规、循环依赖、接口污染、职责越界检测 | 架构一致性守护 |
| `crud-generator` | 数据模型→API/Service/Repository代码生成 | 标准业务模块快速搭建 |

---

## 核心Commands

### 开发流程类

| Command | 功能 | 参数 | 使用场景 |
|---------|------|------|----------|
| `/sketch-dev` | 4阶段精简开发 | `<功能描述>` | 中小型功能、需求明确 |
| `/holistic-dev` | 9阶段全面开发 | `<功能描述> [--skip-clarify]` | 复杂功能、跨系统、需深度分析 |
| `/plan` | 独立规划阶段 | `<功能描述> [--output=PLAN.md]` | 需审批后再实现 |
| `/implement` | 基于规划实现 | `[--plan=PLAN.md] [--from-step=N]` | 已有方案执行实现 |
| `/explore` | 代码库探索 | `<功能/模块> [--depth=deep]` | 理解现有代码结构 |
| `/refactor` | 重构辅助 | `<目标> [--scope=file,module]` | 代码重构场景 |

### 质量保障类

| Command | 功能 | 使用时机 |
|---------|------|----------|
| `/review` | 独立代码审查 | 变更后质量检查 |
| `/test-gen` | 分析变更代码，自动生成测试用例 | 新功能完成、覆盖率不足 |
| `/qa-gate` | 全量质量门禁：测试→覆盖率→安全→性能→架构 | PR提交前、发布前 |
| `/security-scan` | 全量安全扫描：SAST+依赖漏洞+敏感信息 | 定期扫描、安全审计 |
| `/perf-check` | 性能分析：热路径、内存风险、SQL性能 | 性能优化、上线前检查 |
| `/tech-debt` | 技术债务盘点：代码异味、过时依赖 | 迭代规划、重构评估 |
| `/pr-ready` | PR就绪检查：测试+覆盖率+审查+规范 | 创建PR前 |

### 日常工具类

| Command | 功能 | 适用场景 |
|---------|------|----------|
| `/db-migrate` | 数据库迁移脚本生成、版本追踪 | Schema变更、数据迁移 |
| `/api-debug` | HTTP请求构建、响应验证、契约检查 | API开发、联调测试 |

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
/plan → 用户审批 → /implement → /test-gen → /review → /qa-gate

快捷模式:
/sketch-dev --include-test

PR准备:
/pr-ready → (自动执行) /test-gen + /security-scan + /review

日常迭代:
/explore → /implement → /review
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
│   └── plugin.json
├── README.md
├── commands/
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
│   └── api-debug.md
└── agents/
    ├── code-explorer.md
    ├── code-architect.md
    ├── code-reviewer.md
    ├── code-tester.md
    ├── context-synthesizer.md
    ├── test-generator.md
    ├── security-scanner.md
    ├── performance-analyzer.md
    ├── architect-guard.md
    └── crud-generator.md
```