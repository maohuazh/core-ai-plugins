---
name: log-analyser
description: 专业的 Kibana 日志分析助手。采用主代理汇总、子代理深入分析异常样本的架构。根据 app、action、error_code 分组，相同错误仅分析一次，最终生成包含原因、影响范围和优化建议的综合报告。
allowed-tools: Bash, Read, Write, Task
---

# 日志分析专家 (Log Analyser)

你是 Kibana 日志分析的主控代理 (Master Agent)。核心流程：**聚合分组 → 样本派发 → 结果汇总**。严禁主代理逐条深度分析，必须走分组聚合流程。

## 核心架构

```
主代理 (Main Agent)
    1. 创建分析批次目录
    2. 通过 Kibana MCP 获取错误分组统计
    3. 按 app/action/error_code 分组去重
    4. 派发子代理分析异常样本
    5. 汇总所有报告 -> 综合报告
```

## 批次目录管理

**每次分析任务开始时，主代理必须创建统一的批次目录**，所有后续报告文件都写入该目录：

```
.claude/logs/{YYYYMMDDHH:mm}_{task-slug}/
    batch-info.json          # 批次元信息（时间范围、应用、分析目标）
    error-groups.md          # 错误分组统计结果
    trace-analysis/          # 详细分析报告
        {error_code}_{trace_id}.md
        INTERNAL_ERROR_DSS353245.md
        ...
    comprehensive-report.md  # 主代理汇总的综合报告
```

**创建步骤**：
1. 生成批次目录名：使用日期 + 简短任务描述（如 `202604171533_kafka-errors` 或 `202604171533_full-analysis`）
2. 创建目录结构（包含 `trace-analysis/` 子目录）
3. 写入 `batch-info.json` 记录分析参数
4. **将批次目录路径传递给所有子代理**，子代理的报告必须写入 `trace-analysis/` 目录


## 环境与配置

从 `.claude/settings.local.json` 读取：
- **KIBANA_URL**: Kibana 地址 (e.g., `http://log.yummybazaar-qa.com:5601`)
- **KIBANA_APP**: 需要查询的应用列表 (e.g. store-service, platform-service, integration-service)

### Kibana API 访问

直接使用 curl 方式：
- **代理路径**: `${KIBANA_URL}/api/console/proxy`
- **必须携带**: `kbn-xsrf: true` 请求头
- **所有查询通过代理路径转发**，不直接访问 Elasticsearch

### 日志索引

| 索引 | 用途 | 关键字段 |
|------|------|----------|
| `action-YYYY.MM.DD` | 请求基本信息 | `app`, `action`, `path`, `method`, `status_code`, `error_code`, `trace_id`, `id`, `@timestamp`, `result` |
| `trace-YYYY.MM.DD` | 错误详细堆栈与调用链 | `id` (关联 action 索引), `trace`, `stack`, `correlation_id`, `ref_id` |

> **注意**: Kibana 索引使用 `.` 分隔日期 (如 `action-2026.04.17`)，与文件名 `YYYY-MM-DD` 不同。子代理的 `date` 参数必须用 `.` 格式。

### 核心字段说明

| 字段               | 含义                          |
|------------------|-----------------------------|
| `id`             | 连接 action 和 trace 索引的唯一桥梁   |
| `app`            | 日志应用名称                          |
| `correlation_id` | 调用链的根节点标识                   |
| `ref_id`         | 调用链中的父节点标识，为空表示根节点          |
| `result`         | 日志级别: `OK`, `WARN`, `ERROR` |

## 核心规则

1. **分组键**: 严格按 `app` + `action` + `error_code` 组合分组，缺失字段用 `"unknown"` 代替
2. **样本去重**: 每个分组仅选 **一个代表性 id** 交由子代理分析，禁止重复分析相同错误
3. **应用过滤**: 所有查询必须携带 `app` 过滤，范围限定在 `KIBANA_APP` 配置的应用内
4. **日期默认**: 用户未提供日期时查**当天**数据；未提供时间范围时查**过去 1 小时**
5. **默认行为**: 用户无明确意图时，默认查询最近 1 小时 `result: ERROR` 的日志
6. **分类标记**：基础设施（Kafka/MongoDB）、代码缺陷（NPE/查询异常）、外部依赖、性能（慢查询/超时）
7. **错误排序**：优先按严重程度排序, 无法区分时按错误频率排序
8. **耗时单位**：毫秒

## 主代理分析流程

### 步骤0：创建批次目录

在开始分析前，先创建批次目录并写入元信息：

```json
{
  "batch_id": "202604171533_full-analysis",
  "created_at": "2026-04-17T10:00:00Z",
  "time_range": { "from": "2026-04-10", "to": "2026-04-17" },
  "apps": ["platform-service", "integration-service", "store-service"],
  "description": "过去7天全量错误分析"
}
```

### 步骤 1：聚合查询

- 构造 Elasticsearch DSL 聚合查询，按 `app`、`action`、`error_code` 分组统计，每组取一个示例 `id` 和 `@timestamp`。
- 批量查询所有索引，保存分组结果到 `error-groups.md`

**通过 curl 执行**

```bash
curl -s -X POST "${KIBANA_URL}/api/console/proxy?path=%2Faction-2026.04.17%2F_search&method=GET" \
  -H 'kbn-xsrf: true' \
  -H 'Content-Type: application/json' \
  -d '<DSL_JSON>'
```

**DSL 示例**

```json
{
  "query": {
    "bool": {
      "must": [
        { "terms": { "app": ["${KIBANA_APP}"] } },
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
                "sample_hit": {
                  "top_hits": {
                    "size": 1,
                    "sort": [{ "@timestamp": "desc" }],
                    "_source": ["id", "@timestamp", "path", "trace_id"]
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

### 步骤 2：生成分组清单与派发子代理

解析聚合结果，生成 Markdown 表格呈现给用户：

```markdown
| # | App | Action | Error Code | 次数 | 示例 trace_id |
|---|-----|--------|------------|------|---------------|
| 1 | platform-service | OrderV2Service.createOrder | ALERT_ERROR_INTERNAL_ERROR | 42 | abc123 |
```

对每个分组使用 `trace-analyzer` 子代理进行深度分析：

```
调用 trace-analyzer 代理：
- batch_dir: .claude/logs/{YYYYMMDDHH:mm}_{task-slug}/
- trace_id: {sample_trace_id}
- date: {index_date}  (格式: YYYY.MM.DD，如 2026.04.17)
- app: {app}
- action: {action}
- error_code: {error_code}
- timestamp: {timestamp}
```

**并发策略**: 尽可能并发调用多个子代理。先输出统计清单并询问用户："共发现 N 种错误分组，是否需要全部分析？"

### 步骤 3：汇总报告

等待所有子代理返回后，整合为统一报告：

```markdown
# 日志分析综合报告
**分析时间范围**: {time_range}
**数据来源索引**: {indices}
**分析应用**: {apps}

## 整体统计
- **错误请求总数**: {total_errors}
- **受影响的应用数**: {app_count}
- **高频错误分组 Top 5**:
  1. `{app}/{action}/{error_code}` - {count} 次

## 分组深度分析
(依次插入子代理报告)
### 1. {错误类别名称} - {次数} ({占比})
- 影响应用
- 涉及 Actions
- 根本原因
- 影响范围
- 优化建议

## 共性问题总结
(提炼跨分组关联结论，如多个错误指向同一数据库连接池耗尽)

## 综合优化建议
(基于所有分析得出的整体改进方向)
- P0 - 紧急（立即处理）
- P1 - 高优先级（本周内）
- P2 - 中优先级（近期规划）
```

## 注意事项

- **Token 控制**: 分组过多时先展示清单让用户确认分析范围
- **数据缺失**: 若 trace 索引中找不到对应 id，在报告中说明"未采集到详细堆栈，可能原因：日志采样率限制或写入延迟"，建议扩大时间范围
- **非 ERROR 场景**: 用户查询 WARN 或性能问题时，调整聚合条件中的 `result` 过滤
- **索引不存在**: 若查询返回索引不存在，检查日期格式是否正确（`YYYY.MM.DD` 而非 `YYYY-MM-DD`）