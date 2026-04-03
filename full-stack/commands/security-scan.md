---
name: security-scan
description: 全量安全扫描，检测漏洞与敏感信息泄露
triggers:
  - /security-scan
  - /security-scan <路径>
parameters:
  - name: 路径
    description: 扫描范围，默认当前目录
  - name: --severity
    description: 最低严重级别 (critical|high|medium|low)
    default: medium
  - name: --include-deps
    description: 包含依赖漏洞检查
    default: true
  - name: --include-secrets
    description: 包含敏感信息检测
    default: true
---

# Security Scan 安全扫描

全面安全检查，识别潜在风险。

## 检查维度

**1. 输入验证**
- SQL注入风险
- XSS跨站脚本
- 命令注入
- 路径遍历

**2. 认证授权**
- 弱密码检测
- 会话管理缺陷
- 权限绕过风险
- JWT配置问题

**3. 敏感数据**
- 硬编码密钥
- 日志敏感信息
- 不安全存储
- 敏感信息泄露

**4. 依赖漏洞**
- CVE漏洞匹配
- 版本安全告警
- 废弃包检测
- 许可证风险

## 输出格式

```markdown
# 安全扫描报告

## 严重 🔴
- [SQL注入] src/api/user.go:78 用户输入直接拼接SQL
  修复方案: 使用参数化查询

## 高危 🟠
- [CVE-2024-1234] lodash@4.17.0 原型污染
  修复方案: npm update lodash@4.17.21

## 中危 🟡
- [硬编码密钥] src/config/db.go:12 API_KEY暴露
  修复方案: 迁移至环境变量
```

## 使用示例

```
/security-scan
/security-scan src/modules/auth --severity=high
/security-scan --include-deps=false
```