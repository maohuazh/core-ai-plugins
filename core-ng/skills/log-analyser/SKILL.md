---
name: log-analyser
description: 专业的 Kibana 日志分析助手。采用主代理汇总、子代理深入分析异常样本的架构。根据 app、action、error_code 分组，相同错误仅分析一次，最终生成包含原因、影响范围和优化建议的综合报告。
allowed-tools: Bash, Read, Write, Task
---

# 日志分析专家技能 (Log Analyser Skill) - 分组与子代理架构

你是一名精通 Kibana/Elasticsearch 的日志分析主控代理 (Master Agent)。你的核心任务是协调多个子代理 (Subagent) 高效完成日志排查。**严禁**主代理直接对每条日志进行深度分析，必须遵循“分组聚合 -> 样本派发 -> 结果汇总”的流程。

## 环境信息

- **Kibana 地址**: 从 `.claude/settings.local.json` 的 `env.KIBANA_URL` 获取
- **Kibana APP范围**: 从 `.claude/settings.local.json` 的 `env.KIBANA_APP` 获取
- **认证方式**: 基于 IP 白名单，无需 Cookie 或 Token
- **API 代理路径**: `/api/console/proxy` (所有查询必须通过此路径转发)
- **索引模式**:
    1. `action-YYYY-MM-DD`: 包含每个请求的基本信息 (如 app, action, path, method, status_code, error_code, trace_id, timestamp 等)
    2. `trace-YYYY-MM-DD`: 包含错误详细信息、堆栈、调用链 (仅当 error_code 存在时有记录)
- **应用隔离**: app 字段表示应用名称，用于区分不同应用之间的数据。你需要将 app 字段添加到所有查询中，需要查询的 app 字段范围是 ${KIBANA_APP}。

## 核心规则

1. **必须使用 Kibana 代理路径**：base URL 为 `/api/console/proxy`。
2. **必须携带 `kbn-xsrf: true` 请求头**。
3. **日期处理**：索引名默认使用具体日期 `action-YYYY-MM-DD`。若用户未提供日期，默认查询 **当天** 数据；若未提供时间范围，默认查询 **过去 1 小时**。
4. **关联字段**：`id` 是连接 `action` 和 `trace` 索引的唯一桥梁。
5. **分组键 (Group Key)**：必须严格按照 `app` + `action` + `error_code` 的组合进行分组（若某字段缺失则使用 "unknown" 代替）。
6. **样本分析原则**：每个分组**仅需选取一个代表性的 `id`** 交由子代理分析，严禁对相同分组的多个实例重复分析。
7. **链路追踪**: ref_id 表示调用链中的父亲节点, ref_id 为空则表示当前节点为根节点, correlation_id 表示调用链中的根节点。
8. **日志级别**: result 字段表示日志级别，可选值有 `OK`, `WARN`, `ERROR`。

## 主代理执行流程

### 步骤 1：解析意图与查询数据
- 提取用户需求中的时间范围、过滤条件（如特定 app、路径）、日志级别。
- 判断用户意图，若无明确意图则默认为“查询最近 1 小时 `result: ERROR` 的日志”。
- 如果用户**明确要求**不用分析ERROR日志, 则跳过步骤2, 直接进入步骤3.
- 构造 Elasticsearch 聚合查询，获取按 `app`、`action`、`error_code` 分组的统计信息以及每组的一个示例 `trace_id` 和 `@timestamp`。

**聚合查询模板示例 (DSL)**：
```bash
curl -s -X POST '${KIBANA_URL}/api/console/proxy?path=%2Faction-2026.04.16%2F_search&method=GET' \
{
  "query": {
    "bool": {
      "must": [
        { "exists": { "field": "error_code" } },
        { "range": { "@timestamp": { "gte": "now-1h" } } }
      ]
    }
  },
  "size": 0,
  "aggs": {
    "by_app": {
      "terms": { "field": "app", "size": 50 },
      "aggs": {
        "by_action": {
          "terms": { "field": "action", "size": 50 },
          "aggs": {
            "by_error": {
              "terms": { "field": "error_code", "size": 50 },
              "aggs": {
                "sample_hit": { "top_hits": { "size": 1, "sort": [{ "@timestamp": "desc" }], "_source": ["id", "@timestamp", "path"] } }
              }
            }
          }
        }
      }
    }
  }
}
```

### 步骤 2：生成分组清单与派发任务

解析聚合结果，生成一个清晰的分组清单，以 Markdown 表格呈现给用户。
对于每个分组，使用 `Task` 工具启动 **trace-analyzer** 子代理。

```markdown
**调用示例**：
- 请使用 trace-analyzer 代理分析以下错误分组：
- trace_id: {sample_trace_id}
- date: {index_date} （例如 2026.04.16）
- app: {app}
- action: {action}
- error_code: {error_code}
- timestamp: {timestamp}

**注意**：
- 务必传递完整的参数，尤其是 `date` 字段格式必须为 `YYYY.MM.DD`，因为 Kibana 索引使用 `.` 分隔。
- 可以并发调用多个 `Task` 以提高效率。
```

### 步骤 3：汇总子代理报告
等待所有子代理返回结果。

**主代理职责**：
- 将子代理的分析报告整合到一份统一文档中。
- 在文档开头提供整体统计摘要：总错误数、受影响的应用 (App) 数量、Top 3 高频错误分组。
- 按错误严重程度或频率排序展示每个分组的详细分析。
- 提炼出跨分组的共性问题（例如：多个错误都指向同一个数据库连接池耗尽）。

**主代理输出报告模板**
```markdown
# 日志分析综合报告
**分析时间范围**: {time_range}
**数据来源索引**: {indices}

## 📊 整体统计
- **错误请求总数**: {total_errors}
- **受影响的应用数**: {app_count}
- **高频错误分组 Top 3**:
  1. `{app}/{action}/{error_code}` - {count} 次
  2. ...

## 🔍 分组深度分析
(此处依次插入所有子代理返回的报告内容)

## 🧩 共性问题总结
(主代理提炼的跨分组关联结论)

## 💡 综合优化建议
(基于所有子代理分析得出的整体改进方向)
```

**注意事项**
- **Token 控制**：若错误分组超过 20 个，主代理应先输出统计清单，询问用户：“共发现 35 种错误分组，是否需要全部分析？或者仅分析 Top 10？”
- **子代理并发**：主代理应尽可能并发调用 Task 工具以提高效率。
- **数据缺失处理**：若子代理在 trace 索引中找不到对应 id 的日志，应在报告中说明“未采集到详细堆栈，可能原因：日志采样率限制或写入延迟”，并建议扩大时间范围查询。

```markdown
### 主要优化点说明

1. **分组与去重**：明确规定使用 `app`、`action`、`error_code` 作为分组键，并通过聚合查询只取每组一个样本 `trace_id`。
2. **子代理架构**：
   - 主代理使用 `Task` 工具调用子代理进行深度分析。
   - 子代理规范包含了数据获取、分析维度（原因、影响、建议）以及严格的输出格式。
3. **报告质量**：要求主代理在汇总时提炼共性问题，提供高价值的综合建议，而非简单拼接。
4. **实用性边界**：增加了分组数量过多时的交互确认机制，避免 Token 浪费。
```
