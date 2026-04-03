---
name: sketch-dev
description: 4阶段精简开发流程，适合中小型功能
triggers:
  - /sketch-dev <功能描述>
parameters:
  - name: 功能描述
    required: true
    description: 要开发的功能简述
  - name: --skip-review
    description: 跳过代码审查阶段
  - name: --include-test
    description: 包含测试生成
---

# Sketch Dev 精简开发流程

4阶段快速开发，适合需求明确的中小型功能。

## 执行阶段

**Phase 1: Explore** (code-explorer)
- 分析相关代码路径
- 识别需修改文件
- 输出：必读文件清单

**Phase 2: Plan** (code-architect)
- 设计实现方案
- 定义修改范围
- 输出：实现蓝图

**Phase 3: Implement** (自主实现)
- 按蓝图编写代码
- 遵循项目规范
- 输出：代码变更

**Phase 4: Review** (code-reviewer)
- 多维度审查
- 置信度过滤≥80
- 输出：问题清单

## 使用示例

```
/sketch-dev 添加用户登录日志记录
/sketch-dev 实现商品搜索功能 --include-test
/sketch-dev 修复订单状态同步问题 --skip-review
```