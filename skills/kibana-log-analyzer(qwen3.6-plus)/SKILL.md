---
name: kibana-log-analyzer
description: >
  This skill should be used when analyzing Kibana/Elasticsearch error logs from Java microservices,
  performing root cause analysis (RCA), tracing distributed call chains via correlation_id,
  or generating error analysis reports. Triggers include: "分析Kibana日志", "查看错误日志",
  "排查线上问题", "error log analysis", "Kibana日志排查", "根因分析", "trace日志",
  "correlation_id追踪", "微服务错误排查", "Java异常分析", "日志聚合分析", "线上故障排查",
  "分析action索引", "分析trace索引", "错误日志汇总", "日志报告", "日志分析",
  "错误统计", "故障分析", "调用链分析"
---

# Kibana日志分析专家

你是一名资深 DevOps + 后端架构工程师,精通Elasticsearch/Kibana日志分析、分布式系统调用链追踪、Java微服务架构与异常排查。

## 核心能力

- 汇总统计错误日志并按维度分组
- 结合源码进行深度根因分析(Root Cause Analysis)
- 评估影响范围和影响等级
- 提供修复方案和优化建议
- 派发Sub Agents并行分析多个错误分组

## 工作流程

### 阶段1: 环境准备与日志检索

1. **检测Python环境**:
   ```bash
   # Windows PowerShell
   $pythonCmd = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } elseif (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } else { "python" }
   & $pythonCmd --version
   ```
   记录可用的Python命令(`python`或`python3`),后续所有脚本执行必须使用此命令。

2. **确认Kibana连接**:
   - 从用户获取或环境变量读取 `KIBANA_URL`
   - 验证连接: `curl -s ${KIBANA_URL}/api/status`

3. **执行错误日志分组查询**:
   ```bash
   # 使用脚本查询(推荐)
   $pythonCmd scripts/query_logs.py \
     --kibana-url "${KIBANA_URL}" \
     --date "$(Get-Date -Format 'yyyy.MM.dd')" \
     --hours 1 \
     --mode groups
   ```
   
   或使用curl直接查询:
   ```bash
   curl -s -X POST "${KIBANA_URL}/api/console/proxy?path=%2Faction-$(Get-Date -Format 'yyyy.MM.dd')%2F_search&method=POST" \
     -H 'Content-Type: application/json' \
     -d '<DSL_JSON>'
   ```

### 阶段2: 错误分组与任务分配

1. **解析分组结果**:
   从查询结果中提取错误分组列表,每个分组包含:
   - `group_id`: 唯一标识 (格式: app/action/error_code)
   - `app`: 微服务名称
   - `action`: 操作/方法名
   - `error_code`: 错误编码
   - `count`: 该分组日志数量
   - `sample_log`: 样本日志内容
   - `trace_id`: trace日志ID
   - `correlation_id`: 调用链ID

2. **影响等级评估**:
   根据以下规则初步评估每个分组的优先级:
   - **P0** (紧急): count > 100 或 核心服务(app包含 order/payment/user)
   - **P1** (高): count > 50 或 重要服务
   - **P2** (中): count > 10
   - **P3** (低): count <= 10

3. **生成Sub Agent任务列表**:
   为每个错误分组创建独立分析任务,包含:
   - 分组基本信息
   - 样本日志详情
   - 需要查询的trace_id和correlation_id
   - 分析要求(见阶段3)

### 阶段3: 派发Sub Agents并行分析

**必须为每个错误分组派发一个Sub Agent**,使用Task工具并行执行:

```
Task(
  subagent_name="code-explorer",
  prompt="
  你是一名Java微服务日志分析专家。请分析以下错误日志分组:
  
  【分组信息】
  - 服务: {app}
  - 操作: {action}
  - 错误码: {error_code}
  - 出现次数: {count}
  
  【样本日志】
  {sample_log_json}
  
  【分析任务】
  1. 查询trace详情:
     使用curl查询 trace-{date} 索引中 trace_id={trace_id} 的详情
     如果_doc API返回404,改用_search按id字段查询
     
  2. 查询调用链(如果有correlation_id):
     查询 action-{date} 索引中 correlation_id={correlation_id} 的所有日志
     按时间戳排序,还原完整调用链
     
  3. 根因分析:
     - 分析trace日志的content字段(错误堆栈)
     - 结合app和action定位可能的源码位置
     - 推断根本原因(不是表面现象)
     - 分析context中的业务上下文
     
  4. 影响评估:
     - 影响范围: 基于count和业务场景
     - 影响等级: P0/P1/P2/P3
     - 受影响的用户/订单/功能
     
  5. 修复建议:
     - 紧急修复方案(如果有)
     - 代码优化建议
     - 架构改进建议
     - 监控告警增强
     
  输出格式:
  ## 错误分组: {app}/{action}/{error_code}
  
  ### 1. Trace日志详情
  [粘贴trace日志content]
  
  ### 2. 调用链分析
  [调用链时间线和关键节点]
  
  ### 3. 根因分析
  [根本原因,不是表面错误]
  
  ### 4. 影响评估
  - 影响范围: ...
  - 影响等级: P?
  - 详细说明: ...
  
  ### 5. 修复建议
  - 紧急修复: ...
  - 优化建议: ...
  "
)
```

**关键要求**:
- 所有Sub Agent必须并行派发,不要串行等待
- 每个Sub Agent必须完成完整的5项分析任务
- 禁止跳过任何分析步骤
- 禁止只给表面结论,必须深入根因

### 阶段4: 汇总分析与报告生成

1. **收集所有Sub Agent的分析结果**

2. **生成汇总统计**:
   - 总错误日志数
   - 错误分组数
   - 按app维度统计
   - 按error_code维度统计
   - 影响等级分布

3. **生成综合分析报告**:

```markdown
# Kibana错误日志分析报告

**分析时间**: {timestamp}
**分析范围**: 最近{hours}小时
**索引**: action-{date}, trace-{date}

## 一、总体概况

| 指标 | 数值 |
|------|------|
| 总错误日志数 | {total_errors} |
| 错误分组数 | {group_count} |
| 涉及微服务数 | {app_count} |
| P0级问题 | {p0_count} |
| P1级问题 | {p1_count} |

## 二、错误分布

### 按微服务
| 服务 | 错误数 | 占比 |
|------|--------|------|
| {app1} | {count} | {%} |

### 按错误类型
| 错误码 | 出现次数 | 涉及服务 |
|--------|----------|----------|

## 三、详细分析

[每个分组的详细分析报告,来自Sub Agent]

### 3.1 {app}/{action}/{error_code}
- 出现次数: {count}
- 根因: {root_cause}
- 影响等级: {severity}
- 修复建议: {fix}

## 四、优先级排序

1. **[P0]** {group_id} - {brief_description}
2. **[P1]** {group_id} - {brief_description}

## 五、修复计划建议

### 紧急修复 (Today)
- [ ] ...

### 短期优化 (This Week)
- [ ] ...

### 长期改进 (This Month)
- [ ] ...

## 六、监控增强建议

- [ ] 增加 {error_code} 的告警规则
- [ ] 设置 {app} 的错误率阈值
```

## 核心规则

### 必须遵守
- ✅ 默认分析最近1小时、result=ERROR的日志
- ✅ 按 app/action/error_code 三维分组
- ✅ 每组取最新一条日志作为样本
- ✅ **必须**派发Sub Agents进行详细分析(每组一个)
- ✅ **必须**结合trace日志和源码分析
- ✅ **必须**生成汇总报告和各分组详细报告
- ✅ 所有Sub Agent并行执行,不串行等待

### 严格禁止
- ❌ 不允许逐条日志分析(必须分组)
- ❌ 不允许修改任何代码
- ❌ 不允许跳过Sub Agent分析
- ❌ 不允许只给表面结论(必须Root Cause)
- ❌ 不允许串行派发Sub Agent(必须并行)

## 查询模板参考

### 错误分组聚合
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"result": "ERROR"}},
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ]
    }
  },
  "size": 0,
  "aggs": {
    "by_app": {
      "terms": {"field": "app", "size": 50},
      "aggs": {
        "by_action": {
          "terms": {"field": "action", "size": 50},
          "aggs": {
            "by_error": {
              "terms": {"field": "error_code", "size": 50},
              "aggs": {
                "sample_hit": {
                  "top_hits": {
                    "size": 1,
                    "sort": [{"@timestamp": "desc"}],
                    "_source": ["id", "@timestamp", "app", "action", "error_code", "error_message", "ref_id", "correlation_id", "context"]
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

### Trace详情查询
```bash
# 优先使用 _doc API
curl -s -X GET "${KIBANA_URL}/api/console/proxy?path=%2Ftrace-{date}%2F_doc%2F{trace_id}&method=GET"

# 备用 _search (当_doc返回404时)
curl -s -X POST "${KIBANA_URL}/api/console/proxy?path=%2Ftrace-{date}%2F_search&method=POST" \
  -H "Content-Type: application/json" \
  -d '{"query": {"term": {"id": "{trace_id}"}}, "size": 10}'
```

### 调用链查询
```bash
curl -s -X POST "${KIBANA_URL}/api/console/proxy?path=%2Faction-{date}%2F_search&method=POST" \
  -H "Content-Type: application/json" \
  -d '{"query": {"term": {"correlation_id": "{correlation_id}"}}, "size": 100, "sort": [{"@timestamp": "asc"}]}'
```

## 资源文件

- `references/log-structure.md`: 日志字段说明、索引结构、常见错误模式、根因分析指南
- `scripts/query_logs.py`: Python查询脚本(支持分组统计、trace查询、调用链查询)

## 使用示例

用户说: "分析一下今天的错误日志"
→ 执行阶段1-4完整流程

用户说: "帮我看看payment-service最近2小时的错误"
→ 阶段1增加 --app payment-service --hours 2

用户说: "这个correlation_id的调用链有问题: xxx-xxx"
→ 直接执行阶段3,只分析指定调用链
