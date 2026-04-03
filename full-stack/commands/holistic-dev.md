---
name: holistic-dev
description: 9阶段全面开发流程，适合复杂功能与跨系统开发
triggers:
  - /holistic-dev <功能描述>
parameters:
  - name: 功能描述
    required: true
    description: 要开发的功能详述
  - name: --skip-clarify
    description: 跳过需求澄清阶段
  - name: --include-test
    description: 包含测试生成与验证
  - name: --depth
    description: 探索深度 (shallow|medium|deep)
    default: medium
---

# Holistic Dev 全面开发流程

9阶段深度开发，适合复杂功能、跨系统、需深度分析的场景。

## 执行阶段

**Phase 1: Clarify** (需求澄清)
- 识别模糊点
- 确认边界条件
- 输出：明确需求清单

**Phase 2: Explore** (code-explorer)
- 深度代码分析
- 架构层次映射
- 输出：架构理解报告

**Phase 3: Analyze** (code-architect)
- 多方案比较
- 技术选型建议
- 输出：方案对比矩阵

**Phase 4: Plan** (code-architect)
- 详细实现计划
- 文件修改序列
- 输出：实现蓝图+构建序列

**Phase 5: Design Review** (可选)
- 架构评审
- 风险识别
- 输出：设计评审报告

**Phase 6: Implement** (自主实现)
- 按序列编写代码
- 遵循架构约束
- 输出：代码变更

**Phase 7: Test** (code-tester + test-generator)
- 生成测试用例
- 执行验证
- 输出：测试报告

**Phase 8: Review** (code-reviewer)
- 多维度审查
- 置信度过滤
- 输出：问题清单

**Phase 9: Synthesize** (context-synthesizer)
- 整合阶段输出
- 生成变更总结
- 输出：完整开发报告

## 使用示例

```
/holistic-dev 实现多租户权限系统
/holistic-dev 重构支付模块支持多渠道 --include-test
/holistic-dev 添加实时消息推送功能 --skip-clarify --depth=deep
```