# Hooks - 事件层

Claude Code 事件钩子，在 AI 会话的关键时刻自动执行。

## Hook 事件

| 事件 | 触发时机 | 作用 |
|------|----------|------|
| `SessionStart` | 会话开始 | 项目检测、环境初始化 |
| `UserPromptSubmit` | 用户提交 prompt | 规则注入、上下文提醒 |
| `PreToolUse` | AI 调用工具前 | 编辑前合规检查 |
| `PostToolUse` | AI 调用工具后 | 编辑后增量扫描 |
| `Stop` | 每轮回复结束 | 轻量检查（必须检查 `stop_hook_active` 防循环） |

> ⚠️ 注意：`Stop` 在**每轮回复结束**时触发，不是会话结束。需要会话级汇总请用 `SessionEnd`。
> `Stop` hook 必须检查 `stop_hook_active` 输入字段，避免死循环（系统上限 8 次 block）。

## 共享库

`_lib/` 目录包含各 hook 共用的基础设施：

- `gate_runner.py` - 统一门禁执行引擎
- `project_detector.py` - 项目类型检测
- `rule_loader.py` - 规则加载器
- `diff_parser.py` - Git diff 解析
- `report_formatter.py` - 报告格式化
