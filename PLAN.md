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

### Step 1 — 项目骨架 ✅ 文件已创建，待 git commit
- [x] 1.1 创建 `.claude-plugin/plugin.json`
- [x] 1.2 创建目录占位 + 各目录 README.md（hooks/README 中"Stop=会话结束"的表述需更正：Stop 每轮触发）
- [x] 1.3 创建 `core-ai-harness/README.md`
- [ ] 1.4 删除多余的 `skills/commands/` 空占位目录
- [ ] 1.5 Git commit: `feat: scaffold core-ai-harness plugin structure`

### Step 2 — 共享库 `_lib/`（stdlib-only，含单测）
- [ ] 2.1 `__init__.py` + 模块公共路径解析（用 `__file__` 推导插件根，不用 `${CLAUDE_PLUGIN_ROOT}`）
- [ ] 2.2 `gate_runner.py` — 统一执行引擎 + CLI
  - CLI：`python3 gate_runner.py --gate ast-grep --scope changed|files|all [--json] [--files f1,f2]`
  - 读 `gates/config.toml` 决定启用门禁（含 profile 过滤：`default` vs `fbr`）
  - 调用各 runner，把输出归一化为 Finding 结构（D4）
  - 对缺失依赖（如 sg 未装/JAR 缺失）返回 `skipped` 状态而非报错
- [ ] 2.3 `project_detector.py` — build.gradle.kts→java/gradle、pom.xml→java/maven、package.json→node/ts；返回 {type, build_tool, modules[]}
- [ ] 2.4 `rule_loader.py` — 读 rules/*.md 元数据；合并插件默认 + 目标项目 `.claude/gates.toml` overrides
- [ ] 2.5 `diff_parser.py` — git diff → [{file, added_lines, removed_lines}]，支持 staged/unstaged/commit
- [ ] 2.6 `report_formatter.py` — terminal/Markdown/JSON 三格式 + ERROR/WARNING/HINT 汇总
- [ ] 2.7 `tests/test_*.py`（stdlib unittest）：gate_runner 归一化、diff_parser、overrides 合并
- 验收：`python3 -m unittest discover tests` 全绿；`gate_runner.py --json` 输出合法 Finding schema
- [ ] 2.8 Git commit: `feat: add _lib shared infrastructure for hooks and skills`

### Step 3 — Rules 认知层（含交付机制）
- [ ] 3.1 `rules/README.md` — 写明三通道交付（见目录结构注释）+ "Rules 写意图、Gates 写精确匹配"的分工
- [ ] 3.2 `rules/fp-paradigm.md` — 不可变数据/纯函数/Stream API；禁止清单（传统 for、while、i++、参数修改、返回 null）；务实例外（效果边界适配器、性能敏感原始数组）；与 sg 规则一一对应
- [ ] 3.3 `rules/architecture.md` — Controller→Service→Repository 依赖方向；禁止 Web 层碰存储
- [ ] 3.4 `rules/security.md` — 禁硬编码密钥/密码、SQL 拼接、RuntimeException 兜底
- [ ] 3.5 `rules/code-style.md` — 命名、import 顺序、方法长度
- 验收：每个文件 ≤120 行（SessionStart 摘要的 token 预算）；追加到目标项目 `.claude/rules/` 后新会话可见
- [ ] 3.6 Git commit: `feat: add AI agent rules for FP, architecture, security, and code style`

### Step 4 — Gates 最小骨架（ast-grep 垂直切片）
- [ ] 4.1 `gates/config.toml` — 只启用 ast-grep（default profile）
- [ ] 4.2 `gates/ast-grep/runner.sh` — `sg scan --json` 封装：文件列表或 `--changed`；输出归一化 findings；ERROR 数 >0 时 exit 1（供 CI/手动场景），hook 场景由 gate_runner 捕获不外泄
- [ ] 4.3 `sgconfig.yaml` — 精简为 ast-grep 真实 schema（ruleDirs；用 `languageGlobs` 限定 `*.java`）
- [ ] 4.4 迁移 3 条核心 FP 规则：`no-traditional-for-loop` / `no-parameter-mutation` / `no-mutable-accumulator`
  - （`no-null-return` 文件在源项目缺失 → Step 7.1 按 sg_rules/README 描述重建）
- [ ] 4.5 `tests/fixtures/` — 每个 rule 一个必触发的坏样本 + 一个干净的对照样本
- 验收：`sg scan tests/fixtures/BadLoop.java` 报 ERROR；`gate_runner.py --scope files` 输出对应 findings；干净样本 0 误报
- [ ] 4.6 Git commit: `feat: minimal gates skeleton with ast-grep and 3 core FP rules`

### Step 5 — Hooks 基础版（核心闭环）
- [ ] 5.1 `hooks/hooks.json` — `PostToolUse` matcher `"Edit|Write"` → post_edit_gate.py（MultiEdit 已移除，勿再挂）；`SessionStart` → session_start.py；每 hook `timeout: 30`
- [ ] 5.2 `post_edit_gate.py` — 编辑后增量扫描
  - stdin JSON 取 `tool_input.file_path`；非 `.java` → 立即 `exit 0` 空输出
  - 调 gate_runner（只扫该文件）；同文件内容 hash 短路防重复扫描（状态存 `/tmp`）
  - **ERROR** → `{"decision":"block","reason":"<findings + 修复提示>"}`（reason 会反馈给 AI 触发自修复；总长控制在 10k chars 内）
  - **WARNING/HINT** → `{"systemMessage":"<汇总>"}`（给用户；不要依赖 PostToolUse 的 additionalContext，issue #24788）
  - 任何异常 → catch-all，`exit 0` 静默（debug 进 stderr），绝不让编辑失败
- [ ] 5.3 `session_start.py` — additionalContext（≤10k）：项目类型 + 可用门禁状态 + 规则摘要；目标项目已有 `.claude/rules/` 时只注入指针
- [ ] 5.4 占位：prompt_guard / pre_edit_check / stop_report（config 中默认 `enabled: false`）
- 验收：`claude --plugin-dir ./core-ai-harness` 启动会话，编辑 fixture 坏样本 → AI 收到 block reason 并自动修复；编辑 `.md` → 零开销
- [ ] 5.5 Git commit: `feat: basic PostToolUse hook with incremental scanning`

### Step 6 — Skills 基础版
- [ ] 6.1 `skills/gate-scanner/SKILL.md` — frontmatter 必须含 `name` + `description`（description 写清触发场景，Claude 靠它自动触发）；body 编排 gate_runner CLI + report_formatter
- [ ] 6.2 `skills/gate-fixer/SKILL.md` — 逐条修复 findings → 复扫验证闭环（fixture 验证）
- [ ] 6.3 占位其余 skill
- 验收：`claude plugin validate` 通过；skill 能被语义触发
- [ ] 6.4 Git commit: `feat: basic gate-scanner and gate-fixer skills`

### Step 7 — 二次完善
- [ ] 7.1 补全 FP 规则：剩余 9 条活跃 + 重建 `no-null-return`（return null → Optional，带 `fix:` auto-fix）；`no-exception-control-flow` 保持禁用（ast-grep 解析限制）
- [ ] 7.2 shape 规则 30 条迁入 `rules/shape/`，仅 `fbr` profile 启用（配置过滤在 gate_runner 实现）
- [ ] 7.3 `gates/security/pattern_scanner.py`（正则：硬编码密钥/SQL 拼接/RuntimeException 兜底）；`diff_reviewer.py` 明确为 skill 编排的 AI 审查步骤，不做 hook
- [ ] 7.4 迁移 lint/error-prone/build 门禁（FBR profile，可选）：
  - runner 脚本入库；`.dist/*.jar` **不入 git**（48MB，且官方建议插件不打包大二进制）
  - `gate-install` 负责从本地 kit 路径复制 JAR（或提供构建说明）；JAR 缺失时 gate 显示 `skipped`
  - 仅 Java/Gradle 项目启用；检测到非 Gradle 项目显示 not-applicable
- [ ] 7.5 完善 hooks：prompt_guard（默认 off）、pre_edit_check（默认 off，仅保护路径拦截）、stop_report（默认 off；Stop 每轮触发 → 只做"本会话存在未解决 ERROR"轻量检查，检查 `stop_hook_active` 防循环，block 上限意识：系统上限 8 次）
- [ ] 7.6 补全 skills（code-review / project-onboard / gate-report）
- [ ] 7.7 `config.toml` 完整 schema：门禁开关、severity 覆盖、profiles（default/fbr）、排除目录
- [ ] 7.8 Git commit: `feat: complete full harness`
- 验收：全量 fixture smoke 通过；`claude plugin validate` 通过；非 FBR 项目 0 shape 误报

### Step 8 — Commands + 安装 + 文档
- [ ] 8.1 `commands/gates.md` — 门禁总览/状态（frontmatter：description + argument-hint + allowed-tools）
- [ ] 8.2 `commands/gate-check.md` — 手动触发扫描
- [ ] 8.3 `commands/gate-install.md` — 一键安装：装 ast-grep、部署 JAR（可选）、复制 rules 到目标项目 `.claude/rules/`、往目标项目 CLAUDE.md/AGENTS.md 追加 Verification gates 契约（幂等，以 fbr-agent-gates README 流程为蓝本）
- [ ] 8.4 仓库根 `.claude-plugin/marketplace.json`（本地 marketplace，含 core-ai-harness 条目）
- [ ] 8.5 完善 `core-ai-harness/README.md`：架构图 + 本地开发流程（`claude --plugin-dir` 调试 / `claude plugin validate` / `claude plugin marketplace add <repo>` + `claude plugin install core-ai-harness@<marketplace>`）+ 安装依赖说明
- [ ] 8.6 Git commit: `feat: add commands, marketplace entry, and complete documentation`
- 验收：从空机器按 README 走通完整安装；可选：`claude plugin eval` 建一个最小评测目录

## 当前进度

**Step 1 文件已创建完成，需要执行：**
```bash
cd /Users/murphy/Code/Personal/core-ai-plugins
git add core-ai-harness PLAN.md
git commit -m "feat: scaffold core-ai-harness plugin structure"
brew install ast-grep   # Step 0
```
然后从 **Step 2** 继续实施。
