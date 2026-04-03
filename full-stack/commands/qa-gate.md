---
name: qa-gate
description: 全量质量门禁检查，PR提交前、发布前执行
triggers:
  - /qa-gate
  - /qa-gate <路径>
parameters:
  - name: 路径
    description: 检查范围，默认当前目录
  - name: --coverage-threshold
    description: 覆盖率阈值 (核心90/重要80/一般60)
  - name: --fail-fast
    description: 首个阻塞项即停止
  - name: --output
    description: 报告输出路径
    default: quality-report.md
---

# QA Gate 质量门禁

全量质量检查流水线，确保代码质量达标。

## 执行阶段

**Stage 1: 测试执行**
- 运行单元测试 (npm test / pytest)
- 运行集成测试
- 收集覆盖率报告

**Stage 2: 覆盖率分析** (coverage-analyzer)
- 解析覆盖率报告
- 识别未覆盖分支
- 门禁判断：
  - 核心: ≥90%
  - 重要: ≥80%
  - 一般: ≥60%

**Stage 3: 安全扫描** (security-scanner)
- SAST静态分析
- 依赖漏洞检查
- 敏感信息检测
- 输出：漏洞清单（CVE编号/严重等级/修复方案）

**Stage 4: 性能分析** (performance-analyzer)
- 热路径识别
- N+1查询检测
- 内存风险标记
- 输出：性能报告（瓶颈位置/优化建议）

**Stage 5: 架构守护** (architect-guard)
- 分层检查
- 依赖方向检查
- 接口边界检查
- 输出：架构违规报告

## 输出格式

```markdown
# 质量报告

## 通过项 ✅
- 单元测试: 156 passed
- 覆盖率: 85% (达标)

## 告警项 ⚠️
- [perf] src/api/handler.go:45 可能存在N+1查询
- [arch] src/infrastructure/db.go 直接引用domain层

## 阻塞项 ❌
- [security] CVE-2024-1234: lodash@4.17.0 存在原型污染
  修复方案: npm update lodash@4.17.21
```

## 使用示例

```
/qa-gate
/qa-gate src/modules/payment --coverage-threshold=90
/qa-gate --fail-fast
```