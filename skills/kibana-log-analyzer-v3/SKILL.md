---
name: kibana-log-analyzer
description: 
  Kibana 日志分析与根因诊断技能。用于检索 Kibana 错误日志、按 app/action/error_code 分组、
  派发多个 SubAgent 并行分析每组日志、结合本地源码进行 Root Cause Analysis，
  最终生成汇总报告。适用于 Java 微服务架构下的分布式调用链追踪与异常排查。
allowed-tools: 
disable: true
---

# Kibana 日志分析 Agent Skill

## 概述

本技能用于自动化执行 Kibana 错误日志的检索、分组、深度分析与根因诊断。
通过并行派发 SubAgent 对每个错误分组进行独立分析，结合本地项目源码，
输出结构化的根因分析报告。

## 何时使用

当需要执行以下任务时触发此技能：
- 分析 Kibana 中的错误日志（result=ERROR）
- 对微服务异常进行根因分析（Root Cause Analysis）
- 排查分布式系统中的调用链问题
- 评估错误日志的影响范围和影响等级
- 结合源码定位 Java 微服务中的 Bug

## 环境变量要求

使用前必须配置以下环境变量：

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `KIBANA_URL` | Kibana 服务地址 | `http://kibana.example.com:5601` |
| `SOURCE_DIR` | 本地项目源码根目录 | `/path/to/project/src` |

## 执行流程

### Phase 1: 错误日志分组统计

1. 读取环境变量 `KIBANA_URL`，若未设置则提示用户配置
2. 确定分析时间范围（默认：最近 1 小时）和日期索引（格式：`yyyy.mm.dd`）
3. 执行 `scripts/query_error_groups.sh` 查询错误日志分组
4. 解析聚合结果，按 `app` → `action` → `error_code` 三级分组
5. 记录每个分组的：
   - 错误日志数量
   - 最新一条日志的 `id`、`correlation_id`、`error_message`
   - 时间分布

### Phase 2: 派发 SubAgent 并行分析

**关键规则：每个错误分组必须派发一个独立的 SubAgent 进行分析，禁止跳过或合并。**

对每个错误分组，执行以下操作：

1. **准备分析上下文**
   - 从 Phase 1 结果中提取样本日志的 `id` 和 `correlation_id`
   - 使用 `scripts/query_trace_detail.sh` 查询 trace 索引获取详细日志（`content` 字段）
   - 若 trace 查询返回 404，使用 `_search` 按 `id` 字段备用查询

2. **创建 SubAgent 任务**
   
   使用 Task 工具（code-explorer subagent）派发分析任务，Prompt 必须包含：
   
   ```
   你是一名资深 Java 后端架构师，请对以下错误日志分组进行根因分析：
   
   ## 分组信息
   - 服务: {app}
   - 操作: {action}
   - 错误码: {error_code}
   - 错误数量: {count}
   - 时间范围: {time_range}
   
   ## 样本日志
   - ID: {id}
   - 时间: {@timestamp}
   - 错误信息: {error_message}
   - 调用链 ID: {correlation_id}
   
   ## Trace 详细日志
   {trace_content}
   
   ## 分析要求
   1. 结合源码目录 {SOURCE_DIR} 定位出错代码位置
   2. 分析异常堆栈，识别直接原因和根本原因
   3. 评估影响范围（影响用户/订单/请求比例）
   4. 判定影响等级（P0-P3）
   5. 提供修复方案（短期修复 + 长期优化）
   
   ## 输出格式
   生成 Markdown 报告，包含以下章节：
   - 错误概述
   - 调用链分析
   - 源码定位与根因分析
   - 影响范围评估
   - 修复建议
   ```

3. **并行执行**
   - 同时派发所有分组的 SubAgent 任务
   - 等待所有 SubAgent 完成分析
   - 收集各 SubAgent 输出的分析报告

### Phase 3: 生成汇总报告

1. 整合所有 SubAgent 的分析报告
2. 生成全局汇总统计：
   - 总错误日志数量
   - 涉及的服务数量
   - 错误分组数量
   - P0/P1/P2/P3 等级分布
3. 按影响等级排序，优先展示高危问题
4. 输出最终报告到本地 Markdown 文件

## 报告输出规范

### 文件命名

```
kibana-error-report-{YYYYMMDD-HHmmss}.md
```

### 输出位置

默认输出到当前工作目录的 `reports/` 子目录，若不存在则自动创建。

### 报告结构

```markdown
# Kibana 错误日志分析报告

**分析时间**: {timestamp}
**时间范围**: {time_range}
**总错误数**: {total_errors}
**涉及服务**: {app_count} 个
**错误分组**: {group_count} 个

---

## 一、全局统计

| 服务 | 操作 | 错误码 | 错误数 | 影响等级 |
|------|------|--------|--------|----------|
| ... | ... | ... | ... | ... |

## 二、详细分析

### 2.1 [P0] {app}/{action}/{error_code}

> 错误数量: {count} | 最新发生: {timestamp}

#### 错误概述
...

#### 调用链分析
...

#### 源码定位与根因分析
...

#### 影响范围评估
...

#### 修复建议
- **短期**: ...
- **长期**: ...

### 2.2 [P1] ...

---

## 三、总结与建议

### 关键发现
...

### 优先级排序
...

### 后续行动
...
```

## 核心约束

### 必须遵守

✅ 默认分析最近 1 小时内 `result=ERROR` 的日志
✅ 按 `app` + `action` + `error_code` 三级维度分组
✅ 每个分组必须派发 SubAgent 进行独立分析
✅ 必须结合本地源码进行根因分析
✅ 必须生成汇总所有分组的完整报告
✅ 必须评估影响范围和影响等级

### 严格禁止

❌ 不允许逐条日志分析（必须分组后分析）
❌ 不允许修改任何业务代码（只读分析）
❌ 不允许跳过 SubAgent 分析步骤
❌ 不允许只给表面结论（必须深入 Root Cause）
❌ 不允许忽略 trace 索引的详细日志

## 参考文档

- 日志索引结构：`references/log_schema.md`
- 根因分析指南：`references/rca_guide.md`

## 脚本说明

| 脚本 | 用途 |
|------|------|
| `scripts/query_error_groups.sh` | 查询错误日志分组统计 |
| `scripts/query_trace_detail.sh` | 查询 Trace 详细日志 |

### 脚本使用示例

```bash
# 查询错误分组
./scripts/query_error_groups.sh $KIBANA_URL 2026.04.17 1h

# 查询 Trace 详情
./scripts/query_trace_detail.sh $KIBANA_URL 2026.04.17 {trace_id}
```

## 故障排查

### 常见问题

1. **KIBANA_URL 未配置**
   - 提示用户设置环境变量
   - 提供配置示例

2. **Trace 索引查询返回 404**
   - 自动切换为 `_search` 备用查询
   - 记录警告日志

3. **源码目录不存在**
   - 提示用户配置 `SOURCE_DIR`
   - 降级为仅日志分析（不含源码）

4. **SubAgent 分析超时**
   - 设置合理的 `max_turns` 限制
   - 超时后标记为"分析中"并继续其他分组
