---
name: requirement-analyze
description: 分析需求描述，识别功能边界、验收标准与技术风险
triggers:
  - /requirement-analyze <需求描述>
parameters:
  - name: 需求描述
    required: true
    description: 需求文本或用户故事，如"用户登录时记录操作日志"
  - name: --format
    description: 输出格式 (markdown|json)
    default: markdown
  - name: --output
    description: 输出文件路径
    default: REQUIREMENT.md
---

# Requirement Analyze 需求分析

深度分析需求描述，识别模糊点与边界条件，输出结构化需求规格。

## 分析维度

**功能边界**
- 核心功能识别
- 边缘场景枚举
- 排除范围界定

**验收标准**
- 成功条件定义
- 失败条件定义
- 可测量指标

**技术风险**
- 实现复杂度评估
- 技术依赖识别
- 潜在阻碍项

## 输出模板

```markdown
# 需求分析报告

## 功能概述
[需求核心描述]

## 功能边界
### 核心功能
- 功能点1
- 功能点2

### 边缘场景
- 场景1：处理策略
- 场景2：处理策略

### 排除范围
- 不包含的功能点

## 验收标准
### 成功条件
- [ ] 条件1
- [ ] 条件2

### 失败条件
- [ ] 条件1

## 技术风险
| 风险 | 影响等级 | 缓解策略 |
|------|----------|----------|
| 风险1 | 高 | 策略描述 |

## 待澄清问题
- 问题1
- 问题2
```

## 使用示例

```
/requirement-analyze 用户登录时需要记录操作日志，包括登录时间、IP地址、设备信息
/requirement-analyze 实现订单导出功能 --format=json
```

## 与其他命令协作

```
/requirement-analyze → /plan → 用户审批 → /implement
```