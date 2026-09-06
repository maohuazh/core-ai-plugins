# Rules - AI 认知层

自然语言规则文档，AI Agent 在生成代码时自动阅读并遵守。

## 规则文件

- `fp-paradigm.md` - 函数式编程范式
- `architecture.md` - 分层架构约束
- `security.md` - 安全编码策略
- `code-style.md` - 通用代码风格

## 三通道交付机制

Rules 通过三种方式交付给 AI：

### 1. 项目级规则（推荐）
通过 `gate-install` 命令复制规则到目标项目的 `.claude/rules/` 目录。
```bash
claude plugin install core-ai-harness
/gate-install
```
项目级规则会在每次会话开始时自动加载。

### 2. SessionStart 注入
在会话开始时通过 `additionalContext` 注入规则摘要（≤10k 字符）。
由 `hooks/session_start.py` 实现。

### 3. Skills 按需读取
Skills 可以读取完整的规则文件作为参考。

## Rules vs Gates 的区别

```
Rules 说：  "避免使用传统 for 循环，优先使用 Stream API 处理集合操作"
             ↑ 自然语言，AI 理解意图

Gates 说：  pattern: for ($INIT; $COND; $UPDATE) { $BODY }
             ↑ AST pattern，机器精确匹配
```

Rules 是"道德准则"，Gates 是"法律条文"。
