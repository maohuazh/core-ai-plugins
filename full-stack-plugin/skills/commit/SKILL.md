---
name: commit
description: 提交技能。当用户需要创建 Git 提交、编写提交信息、暂存变更时激活。
disable-model-invocation: true
user-invocable: true
allowed-tools: Bash(git status, git diff, git add, git commit, git log)
---

# Git 提交技能

规范化 Git 提交操作，生成符合 Conventional Commits 规范的提交信息。

## Conventional Commits 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 提交类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | feat(auth): add JWT authentication |
| `fix` | 修复 bug | fix(api): resolve null pointer error |
| `docs` | 文档变更 | docs: update README installation steps |
| `style` | 代码格式 | style: fix indentation in utils.ts |
| `refactor` | 代码重构 | refactor(user): extract validation logic |
| `test` | 测试相关 | test(user): add unit tests for service |
| `chore` | 构建/工具 | chore: update dependencies |
| `perf` | 性能优化 | perf(db): optimize query performance |

## 提交流程

### 1. 查看变更状态
```bash
git status
git diff --stat
```

### 2. 分析变更内容
- 识别变更类型（功能/修复/重构等）
- 确定影响范围（模块/文件）
- 提取关键变更点

### 3. 暂存变更
```bash
# 按模块分组暂存
git add src/auth/
git add tests/auth/

# 或全部暂存
git add .
```

### 4. 生成提交信息
基于变更内容自动生成规范化提交信息：

```bash
git commit -m "$(cat <<'EOF'
feat(auth): implement JWT authentication system

- Add JWT token generation and validation
- Implement authentication middleware
- Add user login/logout endpoints
- Include refresh token support

Closes #123
EOF
)"
```

### 5. 验证提交
```bash
git log -1 --pretty=format:"%h - %s"
```

## 提交信息规范

### Subject 行规范
- 使用 imperative 语气（add, not added）
- 不以句号结尾
- 首字母小写
- 长度不超过 50 字符

### Body 规范
- 解释变更的原因和影响
- 与 Subject 行空一行
- 每行不超过 72 字符

### Footer 规范
- 关联 Issue: `Closes #123`
- 标记 Breaking Change: `BREAKING CHANGE: ...`

## 提交示例

### 功能添加
```
feat(user): add user profile management

- Implement profile update API endpoint
- Add profile picture upload functionality
- Create profile page UI component

Closes #456
```

### Bug 修复
```
fix(api): resolve authentication token expiration

Users were unable to refresh expired tokens.
This fix implements proper token refresh logic.

Fixes #789
```

### 重构
```
refactor(service): extract user validation logic

Move validation rules from controller to service layer
for better code organization and reusability.
```

## 工作流程

1. 运行 `git status` 查看变更
2. 运行 `git diff` 分析内容
3. 确定提交类型和范围
4. 暂存相关变更
5. 生成规范化提交信息
6. 执行 git commit
7. 验证提交结果