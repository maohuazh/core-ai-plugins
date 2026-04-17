# core-ng

Claude Code 插件：Kibana 日志分析工具集。

## 安装

此插件仓库包含 `.claude-plugin/`、`.codex/`、`.opencode/` 等标准目录，各工具按自身机制加载。

### Claude Code

```bash
# 方式一：通过 /plugin 命令安装
/plugin marketplace add <your-marketplace-url-or-git-path>
/plugin install core-ng

# 方式二：直接克隆后本地加载
git clone <repo-url> /path/to/core-ai-plugins
# 然后在 Claude Code 项目中指向路径
```

### Codex CLI

```bash
# 克隆后建立 skills 软链接
git clone <repo-url> ~/.codex/core-ng

# macOS / Linux
mkdir -p ~/.agents/skills
ln -s ~/.codex/core-ng/core-ng/skills ~/.agents/skills/core-ng

# Windows (PowerShell)
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
cmd /c mklink /J "$env:USERPROFILE\.agents\skills\core-ng" "$env:USERPROFILE\.codex\core-ng\core-ng\skills"
```

> 重启 Codex 后即可生效。

### OpenCode

在项目根目录或全局 `opencode.json` 中添加 plugin：

```json
{
  "plugin": [
    "core-ng@git+https://github.com/maohuazh/core-ai-plugins.git#main"
  ]
}
```

重启 OpenCode 后自动安装并注册 skills。

> **版本锁定**：将 `#main` 替换为具体 tag，如 `#v1.0.0`。

## 功能

通过 Kibana API 对微服务日志进行聚合分组、样本派发和根因分析，生成结构化的错误报告。

## 架构

```
log-analyser (主代理)
    ├── 聚合分组 → 按 app/action/error_code 去重统计
    ├── 样本派发 → 每个分组选一个代表性 trace_id
    ├── trace-analyzer (子代理) → 深度分析单个错误
    └── 结果汇总 → 生成综合报告
```

## 组件

### Agents

| Agent | 描述 |
|-------|------|
| `log-analyser` | 主控代理，负责错误聚合分组、子代理派发和报告汇总 |
| `trace-analyzer` | 子代理，根据 trace_id 从 Kibana 获取详细日志并结合本地代码进行根因分析 |

### Skills

| Skill | 描述 |
|-------|------|
| `log-analyser` | 日志分析技能入口，触发 log-analyser 代理 |

## 支持的错误类型

- Kafka 相关错误（UNASSIGNED、handler NullPointerException）
- MongoDB 查询异常（MongoCommandException、CollectionNotFoundException）
- NullPointerException
- 性能告警（慢查询、超时）
- 外部集成错误（Square、Stripe 等）

## 配置

在 `.claude/settings.local.json` 中配置：

```json
{
  "KIBANA_URL": "http://xxxxx:5601",
  "KIBANA_APP": "xxxx-service,xxxx-service,xxxx-service"
}
```

## 输出

每次分析生成一个批次目录 `.claude/logs/{YYYYMMDDHHmm}_{task-slug}/`，包含：

- `batch-info.json` — 批次元信息
- `error-groups.md` — 错误分组统计
- `trace-analysis/` — 详细分析报告
- `log-summary.md` — 综合报告
