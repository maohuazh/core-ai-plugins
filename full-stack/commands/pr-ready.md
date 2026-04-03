---
name: pr-ready
description: PR就绪检查，确保代码符合合并标准
triggers:
  - /pr-ready
  - /pr-ready <分支>
parameters:
  - name: 分支
    description: 目标分支，默认main
  - name: --coverage-threshold
    description: 覆盖率阈值
    default: 80
  - name: --skip-test
    description: 跳过测试执行
---

# PR Ready 就绪检查

创建PR前的完整检查清单。

## 检查项

**代码质量**
- [ ] 测试通过
- [ ] 覆盖率达标 (≥阈值)
- [ ] 无高严重级别漏洞
- [ ] 代码审查通过

**规范检查**
- [ ] 提交消息规范
- [ ] 分支命名规范
- [ ] 无冲突

**文档检查**
- [ ] README更新（如需）
- [ ] CHANGELOG更新（如需）
- [ ] API文档更新（如需）

## 执行流程

1. 运行测试套件
2. 检查覆盖率
3. 执行安全扫描
4. 运行代码审查
5. 检查规范
6. 生成PR模板

## 输出格式

```markdown
# PR 就绪检查报告

## 通过项 ✅
- 测试: 156 passed, 0 failed
- 覆盖率: 85%
- 安全: 无高危漏洞

## 待处理项 ⏳
- [ ] 更新CHANGELOG.md

## PR模板
### Changes
- feat: 添加用户登录日志记录

### Test Plan
- [x] 单元测试通过
- [x] 覆盖率达标
```

## 使用示例

```
/pr-ready
/pr-ready develop --coverage-threshold=90
/pr-ready --skip-test
```