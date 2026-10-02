# Kibana 日志分析 Agent Skill

## 简介

这是一个用于 Kibana 错误日志分析与根因诊断的 Agent Skill。它能够：

- 🔍 **自动检索** Kibana 中的错误日志
- 📊 **智能分组** 按 app/action/error_code 三级维度聚合
- 🤖 **并行分析** 派发多个 SubAgent 同时对每个分组进行深度分析
- 🔬 **根因定位** 结合本地源码进行 Root Cause Analysis
- 📝 **报告生成** 自动生成结构化的 Markdown 分析报告

## 安装

本 Skill 已安装在用户级技能目录：

```
~/.workbuddy/skills/kibana-log-analyzer/
```

## 配置

使用前需要配置以下环境变量：

```bash
# Kibana 服务地址
export KIBANA_URL="http://your-kibana-host:5601"

# 本地项目源码目录（用于根因分析）
export SOURCE_DIR="/path/to/your/project/src"
```

## 使用方法

当需要分析 Kibana 错误日志时，直接告知助手：

> "请分析 Kibana 最近 1 小时的错误日志"

或

> "使用 kibana-log-analyzer 技能分析今天的 ERROR 日志"

助手将自动：
1. 查询错误日志分组
2. 为每个分组派发 SubAgent 并行分析
3. 结合本地源码进行根因诊断
4. 生成汇总报告并保存到本地

## 目录结构

```
kibana-log-analyzer/
├── SKILL.md                      # 核心指令文件
├── scripts/
│   ├── query_error_groups.sh     # 错误日志分组查询
│   ├── query_trace_detail.sh     # Trace 详细日志查询
│   └── generate_report.sh        # 汇总报告生成
├── references/
│   ├── log_schema.md             # 日志索引结构参考
│   └── rca_guide.md              # 根因分析指南
└── assets/
    └── report_template.md        # 报告模板
```

## 核心特性

### 1. 三级分组聚合

按 `app` → `action` → `error_code` 维度自动分组，避免逐条分析。

### 2. SubAgent 并行分析

每个错误分组独立派发 SubAgent，同时执行以下分析：
- 调用链追踪（correlation_id / ref_id）
- Trace 详细日志解析
- 源码定位与根因分析
- 影响范围评估
- 修复方案制定

### 3. 根因分析框架

遵循标准的 RCA 流程：
- 错误堆栈分析
- 上下文参数检查
- 源码逻辑对照
- 影响等级判定（P0-P3）
- 修复方案输出（短期 + 长期）

### 4. 结构化报告

生成包含以下章节的完整报告：
- 全局统计概览
- 每个分组的详细分析
- 调用链可视化
- 源码根因定位
- 影响范围评估
- 优先级排序的修复建议

## 约束与规范

### 必须遵守
✅ 默认分析最近 1 小时的 ERROR 级别日志  
✅ 必须按三级维度分组  
✅ 每个分组必须派发 SubAgent 分析  
✅ 必须结合本地源码  
✅ 必须生成完整汇总报告  

### 严格禁止
❌ 逐条日志分析  
❌ 修改任何业务代码  
❌ 跳过 SubAgent 分析  
❌ 只给表面结论  
❌ 忽略 trace 索引  

## 故障排查

| 问题 | 解决方案 |
|------|----------|
| KIBANA_URL 未配置 | 设置环境变量后重试 |
| Trace 查询 404 | 自动切换为 _search 备用查询 |
| 源码目录不存在 | 提示配置 SOURCE_DIR，降级为纯日志分析 |
| SubAgent 超时 | 标记为"分析中"，继续其他分组 |

## 技术栈

- **Elasticsearch/Kibana**: 日志存储与检索
- **Bash Scripts**: 日志查询与报告生成
- **SubAgent 架构**: 并行分析引擎
- **Markdown**: 报告输出格式

## 适用场景

- Java 微服务架构的异常排查
- 分布式调用链追踪
- 生产环境错误日志的自动化分析
- 根因定位与影响评估
- 周期性日志健康检查

## 许可证

内部工具，供团队使用。
