---
name: dep-check
description: 检查依赖更新、安全漏洞与许可证风险
triggers:
  - /dep-check
  - /dep-check <包名>
parameters:
  - name: 包名
    description: 指定检查的包名，默认检查全部依赖
  - name: --include-licenses
    description: 包含许可证合规检查
    default: true
  - name: --outdated-only
    description: 仅显示过时依赖
    default: false
  - name: --fix
    description: 自动更新无风险的过时依赖
    default: false
---

# Dep Check 依赖检查

全面检查项目依赖的健康状态，识别更新机会、安全风险与许可证问题。

## 检查维度

**版本状态**
- 过时依赖识别
- 最新稳定版本
- 破坏性变更预警

**安全漏洞**
- CVE漏洞匹配
- 漏洞严重等级
- 修复版本建议

**许可证合规**
- 许可证类型识别
- 许可证兼容性分析
- 商业使用风险

**依赖健康**
- 维护状态检查
- 社区活跃度
- 弃用预警

## 输出模板

```markdown
# 依赖检查报告

## 过时依赖

| 包名 | 当前版本 | 最新版本 | 更新类型 | 破坏性变更 |
|------|----------|----------|----------|------------|
| lodash | 4.17.0 | 4.17.21 | patch | 无 |
| axios | 0.21.0 | 1.6.0 | major | 有 - 迁移指南 |

## 安全漏洞

| 包名 | CVE编号 | 严重等级 | 修复版本 | 描述 |
|------|---------|----------|----------|------|
| lodash | CVE-2024-1234 | 高 | 4.17.21 | 原型污染 |

## 许可证合规

| 包名 | 许可证 | 商业使用 | 兼容性 |
|------|--------|----------|--------|
| react | MIT | ✅ 允许 | 兼容 |
| some-gpl-package | GPL-3.0 | ⚠️ 需评估 | 不兼容 |

## 建议

### 立即更新
- lodash@4.17.21 (安全修复)

### 需评估后更新
- axios@1.6.0 (需迁移工作)

### 许可证风险
- some-gpl-package (建议替换为MIT许可的替代方案)
```

## 使用示例

```
/dep-check
/dep-check lodash
/dep-check --outdated-only
/dep-check --fix
```

## 与其他命令协作

```
/tech-debt → /dep-check → /refactor (替换不兼容依赖)
```