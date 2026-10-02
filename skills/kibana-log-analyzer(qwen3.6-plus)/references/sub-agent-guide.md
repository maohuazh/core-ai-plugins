# Sub Agent日志分析指南

本文档供主Agent派发Sub Agent时参考,确保每个Sub Agent执行完整、一致的分析流程。

## Sub Agent任务模板

```
你是一名Java微服务日志分析专家。请完成以下分析任务:

【输入信息】
- 服务名称: {app}
- 操作名称: {action}
- 错误编码: {error_code}
- 出现次数: {count}
- 样本日志ID: {trace_id}
- 调用链ID: {correlation_id}
- 分析日期: {date}

【必须完成的分析步骤】

## 步骤1: 获取Trace日志详情

执行以下curl命令获取详细错误信息:

```bash
# 尝试 _doc API
curl -s -X GET "${KIBANA_URL}/api/console/proxy?path=%2Ftrace-{date}%2F_doc%2F{trace_id}&method=GET"

# 如果返回404或found=false,使用备用查询
curl -s -X POST "${KIBANA_URL}/api/console/proxy?path=%2Ftrace-{date}%2F_search&method=POST" \
  -H "Content-Type: application/json" \
  -d '{"query": {"term": {"id": "{trace_id}"}}, "size": 10}'
```

重点关注返回结果中的 `content` 字段,它包含:
- Java异常堆栈跟踪
- 错误详细描述
- 可能的代码行号

## 步骤2: 追踪完整调用链 (如果有correlation_id)

```bash
curl -s -X POST "${KIBANA_URL}/api/console/proxy?path=%2Faction-{date}%2F_search&method=POST" \
  -H "Content-Type: application/json" \
  -d '{"query": {"term": {"correlation_id": "{correlation_id}"}}, "size": 100, "sort": [{"@timestamp": "asc"}]}'
```

分析调用链:
- 按 @timestamp 排序还原调用顺序
- 通过 ref_id 构建调用树
- 识别失败发生在哪个环节
- 查看上游服务的context信息

## 步骤3: 根因分析 (Root Cause Analysis)

基于trace日志和调用链,进行深度分析:

### 3.1 异常堆栈分析
- 提取最内层异常(根异常)
- 识别异常类型(NullPointerException, TimeoutException等)
- 定位可能的代码位置(类名、方法名、行号)

### 3.2 业务上下文分析
- 查看context中的业务字段(order_id, product_id等)
- 分析是哪个具体业务对象触发的问题
- 判断是数据问题还是代码问题

### 3.3 调用链分析
- 失败发生在调用链的哪个节点
- 上游服务是否正常
- 是否存在级联失败

### 3.4 根因推断
**不要只说表面现象**,必须推断根本原因:

❌ 错误示例: "发生了NullPointerException"
✅ 正确示例: "在OrderService.processOrder()第142行,由于上游返回的customer对象为null,且未做空值检查,导致NPE。根本原因是UserService.getUser()在用户不存在时返回null而非抛出明确异常。"

## 步骤4: 影响评估

### 影响范围
- 受影响的功能模块
- 受影响的用户/订单数量(基于count和context推断)
- 是否影响核心业务流程

### 影响等级判定
| 等级 | 标准 |
|------|------|
| P0 | 核心功能完全不可用,或count>100,或涉及支付/用户/订单核心服务 |
| P1 | 核心功能部分受损,或count>50,或影响大量用户 |
| P2 | 非核心功能异常,或count>10,影响可控 |
| P3 | 轻微异常,不影响主流程,或count<=10 |

## 步骤5: 修复建议

### 5.1 紧急修复 (如果需要)
- 具体的代码修改建议
- 临时规避措施
- 数据修复方案

### 5.2 代码优化
- 空值检查增强
- 异常处理改进
- 日志记录完善

### 5.3 架构改进
- 服务降级策略
- 熔断器配置
- 重试机制优化

### 5.4 监控增强
- 需要新增的告警规则
- 监控指标建议
- 日志记录改进点

## 输出格式要求

必须按以下格式输出分析报告:

```markdown
## 错误分组分析报告: {app}/{action}/{error_code}

### 基本信息
- 服务: {app}
- 操作: {action}
- 错误码: {error_code}
- 出现次数: {count}
- 时间范围: {time_range}

### Trace日志详情
```
[粘贴content字段的完整内容]
```

### 调用链分析
[如果有调用链,按时间顺序列出关键节点]
1. {timestamp} - {app}/{action} - {result}
2. ...

### 根因分析
**根本原因**: [一段话说明根因]

**详细分析**:
- 异常类型: ...
- 发生位置: ...
- 触发条件: ...
- 业务上下文: ...

### 影响评估
- **影响范围**: ...
- **影响等级**: P?
- **评估依据**: ...

### 修复建议
1. **紧急修复**: ...
2. **代码优化**: ...
3. **架构改进**: ...
4. **监控增强**: ...
```

## 质量标准

每个Sub Agent的分析报告必须:
- ✅ 包含完整的trace日志内容
- ✅ 有明确的根因推断(不是表面现象)
- ✅ 有量化的影响评估
- ✅ 有具体可执行的修复建议
- ✅ 结合业务上下文分析
- ❌ 禁止只说"发生了XX异常"
- ❌ 禁止没有根因的泛泛而谈
```
