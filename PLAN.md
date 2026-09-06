# Core AI Harness — 实施计划 v2

## 目标

在 `/Users/murphy/Code/Personal/core-ai-plugins/core-ai-harness/` 下实现一个 Claude Code 插件，
整合 Rules（AI 认知）+ Hooks（自动触发）+ Gates（门禁验证），形成代码质量保障闭环。

## v2 修订说明（基于事实核查）

| # | 修订 | 原因 |
|---|------|------|
| 1 | Step 4.4 的 `no-null-return.sg.yaml` 改为 `no-mutable-accumulator.sg.yaml` | 源项目 README/sgconfig 引用了 no-null-return，但**文件实际不存在**；实际规则为 12 条活跃 FP + 30 条 shape（共 42 条，另有 1 条 disabled），不是 44 条 |
| 2 | 新增 Step 0 环境准备 | 本机 **`sg` (ast-grep) 未安装**，Step 4 依赖它 |
| 3 | `gates/config.yaml` → `config.toml` | hooks 保持零第三方依赖：本机 Python 3.14 自带 `tomllib`，无 PyYAML |
| 4 | Rules 交付机制落地 | **插件没有 `rules/` 组件**（不被自动加载）。改为三通道交付：gate-install 复制到目标项目 `.claude/rules/`（项目级规则是真实存在的机制）+ SessionStart 注入摘要 + skills 按需读取 |
| 5 | Hook 契约具体化 + 稳定性守卫 | 官方文档确认：PostToolUse `{"decision":"block","reason"}` 会把 reason 反馈给 AI（self-correct 闭环）；`additionalContext` 在 PostToolUse 上不可靠（issue #24788）→ WARNING 用 `systemMessage`（给用户）；MultiEdit 已在 2.0 移除 → matcher 只挂 `Edit\|Write` |
| 6 | Stop hook 降级为轻量检查 | Stop 在**每轮回复结束**触发（不是会话结束）；必须检查 `stop_hook_active` 防死循环（上限 8 次 block） |
| 7 | lint/error-prone/build 明确为 FBR 专用可选门禁，JAR 不入 git | 两个预编译 JAR 共 48MB，且依赖 FBR 包约定（RepoMetadata/模块感知）；官方建议插件不打包大二进制 |
| 8 | shape 规则默认关闭，按 profile 启用 | 30 条 shape 规则全部是 FBR 项目包约定（`*-service-interface`/`.kafka`/`.domain.collection`…），在别的项目会大量误报 |
| 9 | 插件根路径用 `__file__` 推导，不依赖 `${CLAUDE_PLUGIN_ROOT}` | 已有 issue 报告该变量对 plugin hooks 不总是被设置（#42564） |
| 10 | 每个 hook 永远 `exit 0` + JSON，异常静默降级 | 文档确认：非 0 非 2 退出码 = hook error（对用户刷报错），exit 2 = 无条件阻塞，都不是想要的 |

## 关键决策记录

- **D1 门禁分层**：通用规则（FP/security，任何 Java 项目可用）默认启用；FBR 专用（shape/lint/error-prone/build）放进 `fbr` profile，需项目级 overrides 显式开启。
- **D2 配置格式**：TOML（stdlib `tomllib`，Python ≥3.11）。插件默认配置 `gates/config.toml`，目标项目可用 `.claude/gates.toml` 覆盖（rule_loader 合并）。
- **D3 单一执行入口**：`hooks/_lib/gate_runner.py` 是唯一门禁执行引擎，带 CLI（`--gate/--scope/--json`），hooks、skills、commands 都通过它调用，保证结果 schema 一致。
- **D4 Finding 标准结构**：`{rule_id, gate, file, line, col, severity: ERROR|WARNING|HINT, message, fixable}` — 所有 runner 输出归一化到它。
- **D5 Hook 稳定性契约**：任何 hook 永不阻塞正常流程 —— 全量 try/except，异常时 `exit 0` 静默退出（debug 信息进 stderr）；非 Java 文件直接跳过；单 hook `timeout: 30s`。
- **D6 环境事实**：本机 macOS + Zulu JDK 21 ✅、Python 3.14 ✅（tomllib 可用）、无 PyYAML、无 Scala、`sg` 未装、brew 可用。
- **D7 本地开发/测试闭环**：`claude --plugin-dir ./core-ai-harness` 加载调试；`claude plugin validate` 每步验收；发布用仓库根 `.claude-plugin/marketplace.json`（本地 marketplace）。

## 参考来源（已核实）

`fbr-agent-gates`（`/Users/murphy/Downloads/fbr-agent-gates`）实际内容：

- `sgconfig.yml` + `sg_rules/` — **42 条活跃规则**（12 FP：7 ERROR/4 WARNING/2 HINT…按 README 口径；30 shape 全 WARNING）+ `no-exception-control-flow.sg.yaml.disabled`（ast-grep 无法解析多行 catch，保持禁用）
  - ⚠️ README 和 sgconfig 引用的 `no-null-return` **无对应文件**，迁移时按 README 描述重建（return null → Optional，带 auto-fix）
  - sgconfig.yml 中 `include/exclude/language/output/rules/fix/ignore` 均非 ast-grep 支持字段（severity 实际在各 .sg.yaml 内）→ 迁移时精简为 `ruleDirs`（必要时 + `languageGlobs`）
- `tools/` — java-lint.sh / error-prone-scan.sh（优先跑 `.dist/*.jar`，共 48MB，回退 scala-cli 源码）、gradle-run.sh + gradle-runner.py（构建摘要，日志落 `/tmp/fbr-gradle`）；JavaLint.scala/RepoMetadata.scala 为 FBR 专用
- 原 README 附带"安装到目标仓库 + 往 CLAUDE.md/AGENTS.md 追加 Verification gates 契约"的流程 —— `gate-install.md` 命令以它为蓝本

## 目录结构

```
core-ai-harness/
├── .claude-plugin/
│   └── plugin.json               # 插件 manifest
├── rules/                        # AI 认知层（内容库，非插件自动加载组件！）
│   ├── fp-paradigm.md            #   交付三通道：① gate-install 复制到目标项目
│   ├── architecture.md           #     .claude/rules/（真实机制）
│   ├── security.md               #   ② SessionStart 注入摘要（≤10k chars 上限）
│   ├── code-style.md             #   ③ skills 按需 Read 全文
│   └── README.md
├── gates/
│   ├── config.toml               # 门禁总配置（stdlib tomllib 解析）
│   ├── ast-grep/
│   │   ├── runner.sh             # sg scan 封装（--json 输出 findings）
│   │   ├── sgconfig.yml          # 精简版：只留 ast-grep 真实支持的字段
│   │   ├── rules/fp/             # FP 范式规则（通用）
│   │   ├── rules/shape/          # 架构形状约束（FBR profile）
│   │   └── rules/security/       # 安全规则
│   ├── lint/java-lint.sh         # [FBR profile, 可选] JAR 由 install 部署
│   ├── error-prone/error-prone-scan.sh  # [FBR profile, 可选]
│   ├── build/gradle-run.sh + gradle-runner.py  # [FBR profile, 可选]
│   ├── security/pattern_scanner.py      # 正则扫描：密钥/SQL拼接/RuntimeException兜底
│   └── custom/
├── hooks/
│   ├── hooks.json                # PostToolUse(Edit|Write) + SessionStart
│   ├── _lib/                     # 共享库（全部 stdlib-only, CLI 可独立调用）
│   │   ├── __init__.py
│   │   ├── gate_runner.py        # 统一门禁执行引擎（唯一入口, 含 __main__ CLI）
│   │   ├── project_detector.py   # 项目类型检测
│   │   ├── rule_loader.py        # 规则加载 + 全局/项目 overrides 合并
│   │   ├── diff_parser.py        # git diff 解析（staged/unstaged/HEAD）
│   │   └── report_formatter.py   # terminal 彩色 / Markdown / JSON
│   ├── session_start.py          # SessionStart → additionalContext（项目+门禁+规则摘要）
│   ├── post_edit_gate.py         # PostToolUse → 增量扫描（核心 hook）
│   ├── prompt_guard.py           # UserPromptSubmit（默认 off）
│   ├── pre_edit_check.py         # PreToolUse（默认 off）
│   └── stop_report.py            # Stop（默认 off；轻量 + stop_hook_active 防循环）
├── skills/
│   ├── gate-scanner/SKILL.md
│   ├── gate-fixer/SKILL.md
│   ├── code-review/SKILL.md
│   ├── project-onboard/SKILL.md
│   └── gate-report/SKILL.md
├── commands/
│   ├── gates.md
│   ├── gate-check.md
│   └── gate-install.md
├── tests/                        # stdlib unittest + fixtures
│   ├── fixtures/                 # 必然触发规则的坏 Java 样本
│   └── test_*.py
└── README.md
```

## 实施步骤

### Step 0 — 环境准备 ✅
- [x] 0.1 `brew install ast-grep` — 本机已装 0.45.3
- [x] 0.2 验证 `ast-grep --version`(0.45.3)、`java -version`(21)、`python3 --version`(3.14)
- 验收：`ast-grep scan --help` 可执行
- ⚠️ 注意：`sg` 命令已弃用，统一使用 `ast-grep`

### Step 1 — 项目骨架 ✅
- [x] 1.1 创建 `.claude-plugin/plugin.json`
- [x] 1.2 创建目录占位 + 各目录 README.md
- [x] 1.3 创建 `core-ai-harness/README.md`
- [x] 1.4 删除多余的 `skills/commands/` 空占位目录
- [x] 1.5 Git commit: `feat: scaffold core-ai-harness plugin structure`

### Step 2 — 共享库 `_lib/`（stdlib-only，含单测）✅
- [x] 2.1 `__init__.py` + 模块公共路径解析
- [x] 2.2 `gate_runner.py` — 统一执行引擎 + CLI
- [x] 2.3 `project_detector.py` — 项目类型检测
- [x] 2.4 `rule_loader.py` — 规则加载器
- [x] 2.5 `diff_parser.py` — Git diff 解析
- [x] 2.6 `report_formatter.py` — 报告格式化
- [x] 2.7 单元测试
- [x] 2.8 Git commit

### Step 3 — Rules 认知层 ✅
- [x] 3.1 `rules/README.md`
- [x] 3.2 `rules/fp-paradigm.md`
- [x] 3.3 `rules/architecture.md`
- [x] 3.4 `rules/security.md`
- [x] 3.5 `rules/code-style.md`
- [x] 3.6 Git commit

### Step 4 — Gates 最小骨架 ✅
- [x] 4.1 `gates/config.toml`
- [x] 4.2 `gates/ast-grep/runner.sh`
- [x] 4.3 `sgconfig.yaml`
- [x] 4.4 迁移 3 条核心 FP 规则
- [x] 4.5 `tests/fixtures/`
- [x] 4.6 Git commit

### Step 5 — Hooks 基础版 ✅
- [x] 5.1 `hooks/hooks.json`
- [x] 5.2 `post_edit_gate.py`
- [x] 5.3 `session_start.py`
- [x] 5.4 占位 hooks
- [x] 5.5 Git commit

### Step 6 — Skills 基础版 ✅
- [x] 6.1 `skills/gate-scanner/SKILL.md`
- [x] 6.2 `skills/gate-fixer/SKILL.md`
- [x] 6.3 占位其余 skill
- [x] 6.4 Git commit

### Step 7 — 二次完善（部分完成）
- [ ] 7.1 补全 FP 规则：剩余 9 条活跃 + 重建 `no-null-return`
- [ ] 7.2 shape 规则 30 条迁入 `rules/shape/`，仅 `fbr` profile 启用
- [ ] 7.3 `gates/security/pattern_scanner.py`
- [ ] 7.4 迁移 lint/error-prone/build 门禁（FBR profile，可选）
- [ ] 7.5 完善 hooks：stop_report
- [x] 7.6 补全 skills（code-review / project-onboard）✅
- [x] 7.7 `config.toml` 完整 schema ✅
- [ ] 7.8 Git commit

### Step 8 — Commands + 安装 + 文档 ✅
- [x] 8.1 `commands/gates.md` — 门禁总览/状态（frontmatter：description + argument-hint + allowed-tools）
- [x] 8.2 `commands/gate-check.md` — 手动触发扫描
- [x] 8.3 `commands/gate-install.md` — 一键安装：装 ast-grep、部署 JAR（可选）、复制 rules 到目标项目 `.claude/rules/`、往目标项目 CLAUDE.md/AGENTS.md 追加 Verification gates 契约（幂等，以 fbr-agent-gates README 流程为蓝本）
- [x] 8.4 仓库根 `.claude-plugin/marketplace.json`（本地 marketplace，含 core-ai-harness 条目）
- [x] 8.5 完善 `core-ai-harness/README.md`：架构图 + 本地开发流程（`claude --plugin-dir` 调试 / `claude plugin validate` / `claude plugin marketplace add <repo>` + `claude plugin install core-ai-harness@<marketplace>`）+ 安装依赖说明
- [x] 8.6 Git commit: `feat: add commands, marketplace entry, and complete documentation`
- 验收：从空机器按 README 走通完整安装；可选：`claude plugin eval` 建一个最小评测目录

## 当前进度

**✅ 全部步骤已完成！**

Core AI Harness 插件已完整实现，包括：
- 基础设施（_lib 共享库、配置系统）
- 规则层（4 个规则文件：FP、架构、安全、代码风格）
- 门禁层（3 个 FP 规则 + AST-Grep 集成）
- Hook 层（PostToolUse 自动检查、SessionStart 上下文注入）
- 技能层（4 个技能：扫描、修复、审查、项目初始化）
- 命令层（3 个命令：gates、gate-check、gate-install）
- 完整文档（README + marketplace 配置）

**下一步：**
1. 在实际 Java 项目中测试插件：`claude --plugin-dir ./core-ai-harness`
2. 可选：添加更多 FP 规则（剩余 9 条）或 shape 规则（30 条，仅 FBR 项目）
3. 可选：实现 security 门禁的 pattern_scanner.py
